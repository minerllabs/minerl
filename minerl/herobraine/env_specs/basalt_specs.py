from typing import List, Optional

import gym

from minerl.env import _fake, _singleagent
from minerl.herobraine.env_spec import EnvSpec
from minerl.herobraine.env_specs import simple_embodiment
from minerl.herobraine.hero import handlers, mc

BUTTON_ACTIONS = set(simple_embodiment.SIMPLE_KEYBOARD_ACTION + ["use"])

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


# Herobraine log Reference: https://gist.github.com/shwang/329b417d9acf25f1ff861f98724efd45
# (old) univ.json reference: https://gist.github.com/shwang/c8a6e78bb95b0f3c7fd13b1b752b3ba5
# Malmo schema reference: https://microsoft.github.io/malmo/0.14.0/Schemas/Types.html#type_ItemType
MAKE_HOUSE_VILLAGE_ITEMS = [
    dict(type="stone_shovel", quantity=1),
    dict(type="stone_pickaxe", quantity=1),
    dict(type="cobblestone", quantity=64),
    dict(type="stone_stairs", quantity=64),
    dict(type="fence", quantity=64),
    dict(type="spruce_fence", quantity=64),
    dict(type="acacia_fence", quantity=64),
    dict(type="glass", quantity=64),
    dict(type="ladder", quantity=64),
    dict(type="torch", quantity=64),
    dict(type="planks", quantity=64),
    dict(type="planks", quantity=64, metadata=1),
    dict(type="planks", quantity=64, metadata=2),
    dict(type="log", quantity=64),  # oak
    dict(type="log", quantity=64, metadata=1),  # redwood
    dict(type="log2", quantity=64),  # acacia
    # TODO(shwang): Deal with this overlap... I should make sure that the handlers
    # don't inappropriately clobber log and log2.

    dict(type="sandstone", quantity=64),
    dict(type="sandstone", quantity=64, metadata=2),
    dict(type="sandstone_stairs", quantity=64),
    dict(type="wooden_door", quantity=64),
    dict(type="acacia_door", quantity=64),
    dict(type="spruce_door", quantity=64),
    dict(type="wooden_pressure_plate", quantity=64),
    dict(type="glass", quantity=64),
    dict(type="sand", quantity=64),
    dict(type="dirt", quantity=64),
    dict(type="red_flower", quantity=64),
    dict(type="flower_pot", quantity=64),
    dict(type="snowball", quantity=3),
]

MAKE_HOUSE_VILLAGE_ITEM_NAMES = [x["type"] for x in MAKE_HOUSE_VILLAGE_ITEMS]

# TypeObservation claims that item list needs to begin with 'none' and end with 'other'.
DEFAULT_EQUIP_ITEMS = ('none', 'air', ) + DEFAULT_ITEMS + ('other', )

obs_handler_inventory = handlers.FlatInventoryObservation(list(DEFAULT_ITEMS))
obs_handler_equip = handlers.EquippedItemObservation(list(DEFAULT_EQUIP_ITEMS))

DEFAULT_OBS_HANDLERS = (obs_handler_inventory, obs_handler_equip)


def _get_keyboard_act_handler(k):
    v = mc.INVERSE_KEYMAP[k]
    return handlers.KeybasedCommandAction(k, v)


act_handlers_keyboard = tuple(
    _get_keyboard_act_handler(k) for k in BUTTON_ACTIONS)
act_handler_camera = handlers.CameraAction()
act_handler_equip = handlers.EquipAction(list(DEFAULT_EQUIP_ITEMS))

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
                self._steps_till_done -= 1  # pytype: disable=unsupported-operands
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

    LOW_RES_SIZE = 64
    HIGH_RES_SIZE = 1024

    def __init__(
            self,
            name,
            demo_server_experiment_name,
            high_res: bool,
            max_episode_steps=2400,
    ):
        assert "/" not in demo_server_experiment_name
        if high_res:
            # update env and demo identifiers to include HighRes
            task, ver = name.split('-')
            name = task + "HighRes-" + ver
            demo_server_experiment_name += "-highres"
        self.demo_server_experiment_name = demo_server_experiment_name
        self.high_res = high_res
        self.pov_size = self.HIGH_RES_SIZE if high_res else self.LOW_RES_SIZE
        super().__init__(name=name, max_episode_steps=max_episode_steps)


    def is_from_folder(self, folder: str) -> bool:
        # Implements abstractmethod.
        return folder == self.demo_server_experiment_name

    def _entry_point(self, fake: bool) -> str:
        # Don't need to inspect `fake` argument here because it is also passed to the
        # entrypoint function.
        return BASALT_GYM_ENTRY_POINT

    def create_observables(self):
        obs_handler_pov = handlers.POVObservation([self.pov_size] * 2)
        return [obs_handler_pov] + list(DEFAULT_OBS_HANDLERS)

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

    def get_blacklist_reason(self, npz_data: dict) -> Optional[str]:
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

    def __init__(self, high_res=False):
        super().__init__(
            name="MineRLBasaltFindCaves-v0",
            demo_server_experiment_name="findcaves",
            max_episode_steps=2400,
            high_res=high_res,
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

    def __init__(self, high_res):
        super().__init__(
            name="MineRLBasaltMakeWaterfall-v0",
            demo_server_experiment_name="waterfall",
            max_episode_steps=12000,
            high_res=high_res,
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

    You can't have more than one type of animal in your enclosed area.

    Allowed animals are chickens, sheep, cows, and pigs.
    """

    def __init__(self, high_res):
        super().__init__(
            name="MineRLBasaltPenAnimals-v0",
            demo_server_experiment_name="pen_animals",
            max_episode_steps=12000,
            high_res=high_res,
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
