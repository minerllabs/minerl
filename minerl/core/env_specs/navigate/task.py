from typing import List

from minerl.core.env_specs.env_spec import EnvSpec


class NavigateEnv(EnvSpec):
    def __init__(self, name, resolution, episode_length, ms_per_tick, no_pitch=False,
                 min_radius=64, max_radius=64, randomize_compass_target=False, 
                 dense_reward=False, observe_distance=False):
        self.resolution = tuple(resolution)
        self.ms_per_tick = ms_per_tick
        self.episode_len = episode_length
        self.no_pitch = no_pitch
        self.observe_distance = observe_distance
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.dense_reward = dense_reward
        self.randomize_compass_target = randomize_compass_target
        super().__init__(name)


    def get_filter(self, source):
        pass

    def get_mission_file(self) -> str:
        return "navigation.xml"

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        mission_handlers = [
            handlers.TickHandler(self.ms_per_tick),
            handlers.EpisodeLength(self.episode_len),
            handlers.RewardForTouchingBlock(
                "diamond_block", 100.0, "onceOnly"
            ),
            handlers.NavigateTargetReward(),
            handlers.NavigationDecorator(
                min_radius=self.min_radius,
                max_radius=self.max_radius,
                randomize_compass_target=self.randomize_compass_target
            )
        ]
        if self.dense_reward:
            mission_handlers.append(handlers.RewardForWalkingTowardsTarget(
                reward_per_block=1, reward_schedule="PER_TICK"
            ))
        return mission_handlers


    def (self) -> List[herobraine.hero.AgentHandler]:
        observables = [
            handlers.POVObservation(self.resolution),
            handlers.CompassObservation()]
        if self.observe_distance:
            observables.append(handlers.CompassDistanceObservation())
        return observables

    def create_actionables(self) -> List[herobraine.hero.AgentHandler]:
        actionables = [
            handlers.KeyboardAction("move", "S", "W"),
            handlers.KeyboardAction("strafe", "A", "D"),
            handlers.KeyboardAction("jump", "SPACE"),
            # handlers.KeyboardAction("crouch", "SHIFT"),
            # handlers.KeyboardAction("attack", "BUTTON0"),
            # handlers.KeyboardAction("use", "BUTTON1"),
        ]
        if not self.no_pitch:
            actionables += [handlers.MouseAction("pitch", "cameraPitch")]

        actionables += [handlers.MouseAction("turn", "cameraYaw")]
        return actionables
