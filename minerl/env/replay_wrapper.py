import gym
import json
import numpy as np
from copy import deepcopy
from minerl.herobraine.hero import mc, handlers
from collections import defaultdict, deque



class ReplayWrapper(gym.Wrapper):
    """
    Generic replay wrapper base class.
    Implements logic of acting with the recorded actions
    instead of policy actions for first N steps of the episode,
    where N is the number of steps in the loaded trajectory,
    abstracted away from the details of the environment.

    :param replay_file: path to the file with recorded actions. Recording
                         is assumed to be in jsonl format, where each line
                         is a json-encoded action.

    :param max_steps:   max number of steps to replay. If the recorded trajectory
                        contains more than this number of steps, the rest are
                        truncated.

    :param replay_on_reset: whether the replay is implemented in reset() method, or
                            step-by-step (in step() method via overriding ac argument
                    

    """

    # this key is added to the info dict to indicate
    # whether replaying is active and if policy actions are ignored
    IGNORE_POLICY_ACTION = "replay_ignored_policy_action"

    def __init__(self, env, replay_file, max_steps=None, replay_on_reset=False):
        super().__init__(env)
        self.max_steps = max_steps
        self.replay_file = replay_file
        # TODO maybe replay at reset should be an int, specifiying how many steps
        # to replay at the reset, and the rest would be replayed via overwriting
        # policy actions
        self.replay_on_reset = replay_on_reset

    def reset(self):
        self.load_actions()
        ob = self.env.reset()
        ob = self.extra_steps_on_reset(ob)
        if self.replay_on_reset:
            while len(self.actions) > 0:
                action, next_action = self.get_action_pair()
                if not self.is_on_trajectory(action):
                    break
                ac = self.replay2env(action, next_action)
                ob, _, done, _ = self.env.step(ac)
                assert not done, "Replay put environment in done state"
        return ob

    def get_action_pair(self):
        replay_action = self.actions.popleft()
        next_action = self.actions[0] if len(self.actions) > 0 else None
        return replay_action, next_action


    def step(self, ac):
        ignore_ac = False
        if len(self.actions) > 0:
            replay_action, next_action = self.get_action_pair()
            if self.is_on_trajectory(replay_action):
                ac = self.replay2env(replay_action, next_action)
                ignore_ac = True
            else:
                self.actions.clear()
        ob, rew, done, info = self.env.step(ac)
        info[self.IGNORE_POLICY_ACTION] = ignore_ac
        return ob, rew, done, info

    def load_actions(self):
        if callable(self.replay_file):
            replay_file = self.replay_file()
        elif isinstance(self.replay_file, str):
            replay_file = self.replay_file
        else:
            raise ValueError("replay_file must be a string or a callable")
        with open(replay_file) as f:
            self.actions = deque([json.loads(l) for l in f.readlines()][:self.max_steps])

    def is_on_trajectory(self, replay_action):
        """
        Used in children to determine if the environment has not deviated
        from the recorded trajectory (otherwise, replay will be stopped)
        """
        raise NotImplementedError()

    def replay2env(self, replay_action, next_action):
        """
        Converts an action from the recording format into the environment format
        """
        raise NotImplementedError()

    def extra_steps_on_reset(self, ob):
        """
        Optional modifier for observations on reset
        Can be used to issue additional actions in case starting state is not
        perfectly recorded.
        """
        return ob


class MinecraftReplayWrapper(ReplayWrapper):
    """
    Minecraft-specific implementation of the ReplayWrapper.
    Staying on the recorded trajectory is judged by difference between
    current vs recorded agent coordinates as well as by differnce between
    current and recorded agent inventories.

    :param replay_file:       see ReplayWrapper
    :param clip_stats:        if True, reported stats are adjusted by the amount at the end of the replay
                              so that various monitors only count stats achieved by the policy, not
                              during the replay.
    :param max_steps:         do not replay for more than this number of steps
    :param gui_camera_scaler: additional factor to multiply replay camera actions when gui is open.
                              Useful when replaying data recorded with older (<=5.8) versions of 
                              minerec recorder (should be set to 0.5)
    """

    def __init__(self, env, replay_file, clip_stats=True, max_steps=None, gui_camera_scaler=1.0, replay_on_reset=False):
        super().__init__(env, replay_file, max_steps=max_steps, replay_on_reset=replay_on_reset)
        self.last_info = None
        self.last_ob = None
        self.clip_stats = clip_stats
        self.multiagent = False
        self.gui_camera_scaler = gui_camera_scaler
        self.mismatched_ticks = 0
        # this is a max number of consecutive ticks that are allowed to mismatch the recording,
        # (in inventory or coordinates), before the replay is stopped
        self.max_mismatched_ticks = 20
        # max difference in coordinates (per axis) that is allowed before agent is considered
        # off-trajectory
        self.max_dcoord = 3
        self._patch_agent_start()

    def is_on_trajectory(self, replay_action):
        """
        Checks if the environment is still following the recorded trajectory
        by comparing recorded and current coordinates, and inventories.
        :param replay_action: current action to be replayed. Assumed to be a dict,
                              with xpos, ypos, zpos, and inventory, that are utilized
                              to compare agent location and inventory to the one reported by env
                            
        """
        if self.last_info is None or self.last_ob is None:
            return True
        if self.multiagent:
            return self.is_on_trajectory_impl(
                replay_action, self.last_ob["agent_0"], self.last_info["agent_0"]
            )
        else:
            return self.is_on_trajectory_impl(
                replay_action, self.last_ob, self.last_info
            )

    def is_on_trajectory_impl(self, replay_action, ob, info):
        max_dcoord = self.max_dcoord
        # agents's current coordinates and inventory are pulled from
        # observation and info after ~previous~ step (hence, self.last_[info|ob] logic)
        location_stats = info["location_stats"]
        x = location_stats["xpos"]
        y = location_stats["ypos"]
        z = location_stats["zpos"]
        yaw = location_stats["yaw"]
        pitch = location_stats["pitch"]
        x1 = replay_action["xpos"]
        y1 = replay_action["ypos"]
        z1 = replay_action["zpos"]
        tick1 = replay_action["tick"]
        yaw1 = replay_action["yaw"]
        pitch1 = replay_action["pitch"]

        if (
            abs(x - x1) > max_dcoord
            or abs(y - y1) > max_dcoord
            or abs(z - z1) > max_dcoord
            or abs(yaw - yaw1) > max_dcoord
            or abs(pitch - pitch1) > max_dcoord
        ):
            print(
                f"Tick {tick1}: Coords mismatch: is {x}, {y}, {z}, {yaw}, {pitch}, should be {x1}, {y1}, {z1}, {yaw1}, {pitch1}"
            )
            self.mismatched_ticks += 1
        elif "inventory" in replay_action and \
          not inventory_matches(ob["inventory"], replay_action["inventory"]):
            print(f"Tick {tick1}: Inventory mismatch")
            self.mismatched_ticks += 1
        else:
            self.mismatched_ticks = 0   
        return self.mismatched_ticks < self.max_mismatched_ticks

    def replay2env(self, replay_action, next_action):
        # TODO: unify with the conversion logic in data reader
        self.last_action = replay_action
        ac = mc.minerec_to_minerl_action(
            replay_action,
            next_action=next_action,
            gui_camera_scaler=self.gui_camera_scaler,
            esc_to_inventory=False
        )
        if self.multiagent:
            ac = {"agent_0": ac}
        return ac

    def step(self, ac):
        ob, rew, done, info = super().step(ac)
        self.update_stats(ob, info)
        if self.clip_stats:
            ob = self._clip_stats(ob)
        return ob, rew, done, info

    def reset(self):
        # need to modify create_agent
        ob = super().reset()
        self.multiagent = "agent_0" in ob
        self.mismatched_ticks = 0
        self.last_ob = ob
        self.last_info = None
        return ob

    def update_stats(self, ob, info):
        replaying = info[ReplayWrapper.IGNORE_POLICY_ACTION]
        if replaying:
            self.last_info = deepcopy(info)
            self.last_ob = deepcopy(ob)
        if self.multiagent:
            info["agent_0"][ReplayWrapper.IGNORE_POLICY_ACTION] = replaying

    def _clip_stats(self, ob):
        """
        Adjusts stats (currently, only inventory) by the amount at the end of the replay
        """
        if self.multiagent:
            return {"agent_0": subtract_stats(ob["agent_0"], self.last_ob["agent_0"])}
        else:
            return subtract_stats(ob, self.last_ob)

    def _patch_agent_start(self):
        old_create_agent_start = self.task.create_agent_start
        def create_agent_start():
            h = old_create_agent_start()
            start_pos = self._get_start_pos()
            start_velocity = self._get_start_velocity()
            if start_pos is not None:
                h.append(handlers.AgentStartPlacement(*start_pos))
            if start_velocity is not None:
                h.append(handlers.AgentStartVelocity(*start_velocity))
            return h
        self.task.create_agent_start = create_agent_start

    def _get_start_pos(self):
        if len(self.actions) == 0:
            return None
        a = self.actions[0]
        return a["xpos"], a["ypos"], a["zpos"], a["yaw"], a["pitch"]
    def _get_start_velocity(self):
        if len(self.actions) < 2:
            return None
        a, a1 = self.actions[0], self.actions[1]
        vx = a1["xpos"] - a["xpos"]
        vy = a1["ypos"] - a["ypos"]
        vz = a1["zpos"] - a["zpos"]
        return vx, vy, vz

    def extra_steps_on_reset(self, ob):
        # make sure agent is sprinting if it was sprinting at the replay boundary
        for i in range(len(self.actions) - 1):
            a, na = self.actions[i], self.actions[i+1]
            sprint_stat = 'minecraft.custom:minecraft.sprint_one_cm'
            if na.get("stats", {}).get(sprint_stat, 0) <= a.get("stats", {}).get(sprint_stat, 0):
                break
            a["keyboard"]["keys"].append("key.keyboard.left.control")
        # TODO implement boat / horse activation
        replay_action = self.actions[0]
        if replay_action.get('isGuiOpen', False):
            # this clause accounts for situation when gui is open at the beginning 
            # of the episode. Saves files do not store gui state; which means when
            # a save file is loaded player / agent is always outside of gui. However,
            # minerec cuts trajectories into 5 minute chunks, and the chunk boundary
            # may happen when the player is in gui. If that happens
            # to be the case, we issue additional actions to pull up the correct type
            # of gui, and move mouse in the correct position
            self.env.step(self.env.action_space.no_op())
            ac = self.env.action_space.no_op()
            # Open inventory or gui ...
            ac['inventory' if replay_action.get('isGuiInventory') else 'use'] = 1
            self.env.step(ac)
            # extra steps are needed because crafting table gui does not open
            # immediately on "use" action (only after hand swing is rendered)
            for _ in range(5):
                self.env.step(self.env.action_space.no_op())
            # Move mouse to a correct position. By default, the center of the screen
            # is at 640, 360, and guiscale = 2. If scaledX and scaledY fields are not
            # available, we'll rely on that
            ma = replay_action["mouse"]
            dx = (ma["x"] - 640) / 2
            dy = (ma["y"] - 360) / 2
            dx = ma.get("scaledX", dx)
            dy = ma.get("scaledY", dy)
            ac = self.env.action_space.no_op()
            ac["camera"] = mc.mouse_to_camera({"dx": dx, "dy": dy})
            ob, _, _, _ = self.env.step(ac)
        return ob
            
            

def subtract_stats(ob, base_ob):
    """
    Subtract stats in base_ob from ob
    """

    for k, v in base_ob["inventory"].items():
        ob["inventory"][k] = max(0, ob["inventory"][k] - v)

    for coord in ("xpos", "ypos", "zpos"):
        ob["location_stats"][coord] -= base_ob["location_stats"]["xpos"]

    item_stats = ["pickup", "break_item", "craft_item", "use_item", "mine_block"]

    # the stats are always increasing, so no need to do max(0, )
    for stat in item_stats:
        for item, quantity in base_ob[stat].items():
            ob[stat][item] = ob[stat][item] - quantity
    return ob


def inventory_matches(inv_ob, inv_json):
    inv_dict = defaultdict(int)
    for itemstack in inv_json:
        inv_dict[itemstack["type"]] += itemstack["quantity"]
    for item, quantity in inv_dict.items():
        if int(inv_ob[item]) != quantity:
            print(f"Inventory mismatch! Item {item}: agent has {inv_ob[item]}, should have {quantity}")
            return False
    return True
