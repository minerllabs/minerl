from typing import List, Optional

import gym
from minerl.env import _fake, _singleagent
from minerl.herobraine.env_spec import EnvSpec

from minerl.herobraine.hero import handlers, mc

BUTTON_ACTIONS = {"forward", "back", "left", "right", "jump", "sneak", "sprint", "attack", "use"}

DEFAULT_ITEMS = (
    "stone_shovel",
    "stone_pickaxe",
    "snowball",
    "cobblestone",
    "stone_pickaxe",
    "water_bucket",
    "bucket",
    "fence",
    "fence_gate",
    "wheat_seeds",
    "carrot",
    "wheat",
)


# TypeObservation claims that item list needs to begin with 'none' and end with 'other'.
DEFAULT_EQUIP_ITEMS = ('none', 'air', ) + DEFAULT_ITEMS + ('other', )

obs_handler_pov = handlers.POVObservation((64, 64))
obs_handler_inventory = handlers.FlatInventoryObservation(DEFAULT_ITEMS)
obs_handler_equip = handlers.EquippedItemObservation(DEFAULT_EQUIP_ITEMS)

DEFAULT_OBS_HANDLERS = (obs_handler_pov, obs_handler_inventory, obs_handler_equip)


def _get_keyboard_act_handler(k):
    v = mc.INVERSE_KEYMAP[k]
    return handlers.KeybasedCommandAction(k, v)


act_handlers_keyboard = tuple(
    _get_keyboard_act_handler(k) for k in BUTTON_ACTIONS)
act_handler_camera = handlers.CameraAction()
act_handler_equip = handlers.EquipAction(DEFAULT_EQUIP_ITEMS)

DEFAULT_ACT_HANDLERS = act_handlers_keyboard + (act_handler_camera, act_handler_equip)


class EndAfterSnowballThrowWrapper(gym.Wrapper):
    def __init__(self, env, episode_end_delay=10):
        super().__init__(env)
        assert episode_end_delay >= 0
        self.episode_end_delay = episode_end_delay
        self._steps_till_done = None

    def reset(self):
        self._steps_till_done = None
        obs = super().reset()
        return obs

    def step(self, action: dict):
        observation, reward, done, info = super().step(action)
        if self._steps_till_done is None:  # Snowball throw hasn't yet been detected.
            if (observation["equipped_items"]["mainhand"]["type"] == "snowball"
                    and action["use"] == 1):
                self._steps_till_done = self.episode_end_delay
        else:  # Snowball throw was detected. We will end episode soon.
            if self._steps_till_done == 0:
                done = True
                self._steps_till_done = None
            else:
                self._steps_till_done -= 1
        return observation, reward, done, info


def _basalt_gym_entrypoint(
        env_spec: "BasaltBaseEnvSpec",
        fake: bool = False,
        end_after_snowball_throw: bool = True,
) -> _singleagent._SingleAgentEnv:
    """Used as entrypoint for `gym.make`."""
    if fake:
        env = _fake._FakeSingleAgentEnv(env_spec=env_spec)
    else:
        env = _singleagent._SingleAgentEnv(env_spec=env_spec)
    if end_after_snowball_throw:
        env = EndAfterSnowballThrowWrapper(env)
    return env


BASALT_GYM_ENTRY_POINT = "minerl.herobraine.env_specs.basalt_specs:_basalt_gym_entrypoint"


class BasaltBaseEnvSpec(EnvSpec):

    def __init__(
            self,
            name,
            demo_server_experiment_name,
            max_episode_steps=2400,
    ):
        assert "/" not in demo_server_experiment_name
        super().__init__(name=name, max_episode_steps=max_episode_steps)
        self.demo_server_experiment_name = demo_server_experiment_name

    def is_from_folder(self, folder: str) -> bool:
        # Implements abstractmethod.
        return folder == self.demo_server_experiment_name

    def _entry_point(self, fake: bool) -> str:
        # Assuming here that `fake` argument gets passed along to entrypoint fn.
        return BASALT_GYM_ENTRY_POINT

    def create_observables(self):
        return DEFAULT_OBS_HANDLERS

    def create_actionables(self):
        return DEFAULT_ACT_HANDLERS

    def create_agent_handlers(self) -> List[handlers.Handler]:
        return []

    def create_server_quit_producers(self) -> List[handlers.Handler]:
        return [
            handlers.ServerQuitFromTimeUp(
                (self.max_episode_steps * mc.MS_PER_STEP)),
            handlers.ServerQuitWhenAnyAgentFinishes()
        ]

    def create_server_decorators(self) -> List[handlers.Handler]:
        return []

    def create_server_initial_conditions(self) -> List[handlers.Handler]:
        return [
            handlers.TimeInitialCondition(
                allow_passage_of_time=False
            ),
            handlers.SpawningInitialCondition(
                allow_spawning=True
            )
        ]

    def auto_blacklist(self, npz_data: dict) -> Optional[str]:
        """
        Some saved demonstrations are bogus -- they only contain lobby frames.

        We can automatically skip these by checking for whether any snowballs
        were thrown.
        """
        # TODO(shwang): Waterfall demos should also check for water_bucket use.
        #               AnimalPen demos should also check for fencepost or fence gate use.
        equip = npz_data.get("observation$equipped_items.mainhand.type")
        use = npz_data.get("action$use")
        if equip is None:
            return f"Missing equip observation. Available keys: {list(npz_data.keys())}"
        elif use is None:
            return f"Missing use action. Available keys: {list(npz_data.keys())}"

        assert len(equip) == len(use) + 1, (len(equip), len(use))

        for i in range(len(use)):
            if use[i] == 1 and equip[i] == "snowball":
                return None
        return "BasaltEnv never threw a snowball"

    def create_mission_handlers(self):
        # Implements abstractmethod
        return ()

    def create_monitors(self):
        # Implements abstractmethod
        return ()

    def create_rewardables(self):
        # Implements abstractmethod
        return ()

    def determine_success_from_rewards(self, rewards: list) -> bool:
        """Implements abstractmethod.

        Basalt environment have no rewards, so this is always False."""
        return False

    def get_docstring(self):
        # Implements abstractmethod
        return self.__class__.__doc__


class FindCavesEnvSpec(BasaltBaseEnvSpec):
    """Find a Cave, and then throw a snowball to end episode."""

    def __init__(self):
        super().__init__(
            name="MineRLBasaltFindCaves-v0",
            demo_server_experiment_name="findcaves",
            max_episode_steps=2400,
        )

    def create_agent_start(self) -> List[handlers.Handler]:
        inventory = [dict(type="snowball", quantity=1)]
        return [handlers.SimpleInventoryAgentStart(inventory)]

    def create_server_world_generators(self) -> List[handlers.Handler]:
        return [handlers.BiomeGenerator("plains")]


class MakeWaterfallEnvSpec(BasaltBaseEnvSpec):
    """
    Make an waterfall and then take an aesthetic picture of it.
    """

    def __init__(self):
        super().__init__(
            name="MineRLBasaltMakeWaterfall-v0",
            demo_server_experiment_name="waterfall",
            max_episode_steps=12000,
        )

    def create_agent_start(self) -> List[handlers.Handler]:
        inventory = [
            dict(type="water_bucket", quantity=1),
            dict(type="cobblestone", quantity=20),
            dict(type="stone_shovel", quantity=1),
            dict(type="stone_pickaxe", quantity=1),
            dict(type="snowball", quantity=1),
        ]
        return [handlers.SimpleInventoryAgentStart(inventory)]

    def create_server_world_generators(self) -> List[handlers.Handler]:
        return [handlers.BiomeGenerator("extreme_hills")]


class PenAnimalsEnvSpec(BasaltBaseEnvSpec):
    """
    Surround two or more animals of the same type in a fenced area (a pen).

    You can't have more than one type of animal in your
    enclosed area.

    Allowed animals are chickens, sheep, cows, and pigs.
    """

    def __init__(self):
        super().__init__(
            name="MineRLBasaltPenAnimals-v0",
            demo_server_experiment_name="pen_animals",
            max_episode_steps=12000,
        )

    def create_agent_start(self) -> List[handlers.Handler]:
        inventory = [
            dict(type="fence", quantity=64),
            dict(type="fence_gate", quantity=64),
            dict(type="carrot", quantity=1),
            dict(type="wheat_seeds", quantity=1),
            dict(type="wheat", quantity=1),
            dict(type="snowball", quantity=1),
        ]
        return [handlers.SimpleInventoryAgentStart(inventory)]


    def create_server_world_generators(self) -> List[handlers.Handler]:
        return [handlers.BiomeGenerator("plains")]
