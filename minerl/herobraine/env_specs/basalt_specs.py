from typing import List, Optional, Sequence

import gym

from minerl.env import _fake, _singleagent
from minerl.herobraine import wrappers
from minerl.herobraine.env_spec import EnvSpec
from minerl.herobraine.env_specs import simple_embodiment
from minerl.herobraine.hero import handlers, mc
from minerl.herobraine.hero.handlers import util

BUTTON_ACTIONS = set(simple_embodiment.SIMPLE_KEYBOARD_ACTION + ["use"])

DEFAULT_ITEMS = (
    "stone_shovel",
    "stone_pickaxe",
    "snowball",
    "cobblestone",
    "water_bucket",
    "bucket",
    "fence",
    "fence_gate",
    "wheat_seeds",
    "carrot",
    "wheat",
)


MAKE_HOUSE_VILLAGE_INVENTORY = [
    dict(type="stone_pickaxe", quantity=1),
    dict(type="stone_axe", quantity=1),
    dict(type="cobblestone", quantity=64),
    dict(type="stone_stairs", quantity=64),
    dict(type="fence", quantity=64),
    dict(type="spruce_fence", quantity=64),
    dict(type="acacia_fence", quantity=64),
    dict(type="glass", quantity=64),
    dict(type="ladder", quantity=64),
    dict(type="torch", quantity=64),
    dict(type="planks", quantity=64, metadata=0),
    dict(type="planks", quantity=64, metadata=1),
    dict(type="planks", quantity=64, metadata=4),
    dict(type="log", quantity=64, metadata=0),  # oak
    dict(type="log", quantity=64, metadata=1),  # spruce
    dict(type="log2", quantity=64, metadata=0),  # acacia
    dict(type="sandstone", quantity=64, metadata=0),
    dict(type="sandstone", quantity=64, metadata=2),
    dict(type="sandstone_stairs", quantity=64),
    dict(type="wooden_door", quantity=64),
    dict(type="acacia_door", quantity=64),
    dict(type="spruce_door", quantity=64),
    dict(type="wooden_pressure_plate", quantity=64),
    dict(type="sand", quantity=64),
    dict(type="dirt", quantity=64),
    dict(type="red_flower", quantity=3),
    dict(type="flower_pot", quantity=3),
    dict(type="cactus", quantity=3),
    dict(type="snowball", quantity=1),
]

MAKE_HOUSE_VILLAGE_ITEM_IDS = util.inventory_start_spec_to_item_ids(
    MAKE_HOUSE_VILLAGE_INVENTORY)

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
        snowball_count = obs["inventory"]["snowball"]
        assert snowball_count == 1, "Should start with a snowball"
        return obs

    def step(self, action: dict):
        observation, reward, done, info = super().step(action)
        if self._steps_till_done is None:  # Snowball throw hasn't yet been detected.
            snowball_count = observation["inventory"]["snowball"]
            if snowball_count == 0:
                # Snowball was thrown -- start the countdown.
                self._steps_till_done = self.episode_end_delay
        elif self._steps_till_done > 0:
            # Snowball throw was detected, counting down.
            self._steps_till_done -= 1  # pytype: disable=unsupported-operands
        else:
            # Snowball throw was detected and countdown is over. End episode.
            done = True
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

    # This was developed as a quick hack to mitigate Village-die-due-to-suffocate-in-wall-on-spawn
    # problem. The telltale sign of immediate death on spawn is no snowball existing in the
    # inventory on the first observation, which raises an AssertionError within
    # EndAfterSnowballThrowWrapper.reset().
    #
    # We wrap every BASALT environment in this wrapper defensively because it is
    # computationally cheap when there is no spawning problem, and we have observed rare
    # (and weird!) instances where even FindCaves-v0 spawns without a snowball.
    env = wrappers.RetryResetOnEarlyDeathWrapper(env)

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
            inventory: Sequence[dict] = (),
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
        self.inventory = inventory  # Used by minerl.util.docs to construct Sphinx docs.
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

    def create_agent_start(self) -> List[handlers.Handler]:
        return [handlers.SimpleInventoryAgentStart(self.inventory)]

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
        equip = npz_data.get("observation$equipped_items$mainhand$type")
        use = npz_data.get("action$use")
        if equip is None:
            return f"Missing equip observation. Available keys: {list(npz_data.keys())}"
        if use is None:
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
        return self.__class__.__doc__


MINUTE = 20 * 60


class FindCaveEnvSpec(BasaltBaseEnvSpec):
    """
.. image:: ../assets/basalt/caves1_0-05.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/caves3_0-30.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/caves4_0-30.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/caves5_0-30.gif
  :scale: 100 %
  :alt:

After spawning in a plains biome, explore and find a cave. When inside a cave, throw a
snowball to end episode.
"""

    def __init__(self, high_res: bool):
        super().__init__(
            name="MineRLBasaltFindCave-v0",
            demo_server_experiment_name="findcaves",
            max_episode_steps=3*MINUTE,
            high_res=high_res,
            inventory=[
                dict(type="snowball", quantity=1),
            ],
        )

    def create_agent_start(self) -> List[handlers.Handler]:
        inventory = [dict(type="snowball", quantity=1)]
        return [handlers.SimpleInventoryAgentStart(inventory)]

    def create_server_world_generators(self) -> List[handlers.Handler]:
        return [handlers.BiomeGenerator("plains")]


class MakeWaterfallEnvSpec(BasaltBaseEnvSpec):
    """
.. image:: ../assets/basalt/waterfall0_0-05.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/waterfall2_0-30.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/waterfall6_0-30.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/waterfall8_0-30.gif
  :scale: 100 %
  :alt:

After spawning in an extreme hills biome, use your waterbucket to make an beautiful waterfall.
Then take an aesthetic "picture" of it by moving to a good location, positioning
player's camera to have a nice view of the waterfall, and throwing a snowball. Throwing
the snowball ends the episode.
"""

    def __init__(self, high_res: bool):
        super().__init__(
            name="MineRLBasaltMakeWaterfall-v0",
            demo_server_experiment_name="waterfall",
            max_episode_steps=5*MINUTE,
            high_res=high_res,
            inventory=[
                dict(type="water_bucket", quantity=1),
                dict(type="cobblestone", quantity=20),
                dict(type="stone_shovel", quantity=1),
                dict(type="stone_pickaxe", quantity=1),
                dict(type="snowball", quantity=1),
            ],
        )

    def create_server_world_generators(self) -> List[handlers.Handler]:
        return [handlers.BiomeGenerator("extreme_hills")]


class PenAnimalsPlainsEnvSpec(BasaltBaseEnvSpec):
    """
.. image:: ../assets/basalt/animal_pen_plains2_0-30.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/animal_pen_plains3_0-30.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/animal_pen_plains_4_0-05.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/animal_pen_plains_4_0-30.gif
  :scale: 100 %
  :alt:

Surround two or more animals of the same type in a fenced area (a pen).
You can't have more than one type of animal in your enclosed area.
Allowed animals are chickens, sheep, cows, and pigs.

Throw a snowball to end the episode.
"""

    def __init__(self, high_res: bool):
        super().__init__(
            name="MineRLBasaltCreatePlainsAnimalPen-v0",
            demo_server_experiment_name="pen_animals",
            max_episode_steps=5*MINUTE,
            high_res=high_res,
            inventory=[
                dict(type="fence", quantity=64),
                dict(type="fence_gate", quantity=64),
                dict(type="carrot", quantity=1),
                dict(type="wheat_seeds", quantity=1),
                dict(type="wheat", quantity=1),
                dict(type="snowball", quantity=1),
            ],
        )

    def create_server_world_generators(self) -> List[handlers.Handler]:
        return [handlers.BiomeGenerator("plains")]


class PenAnimalsVillageEnvSpec(BasaltBaseEnvSpec):
    """
.. image:: ../assets/basalt/animal_pen_village1_1-00.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/animal_pen_village3_0-30.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/animal_pen_village4_0-05.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/animal_pen_village4_1-00.gif
  :scale: 100 %
  :alt:

After spawning in a plains village, surround two or more animals of the same type in a
fenced area (a pen), constructed near the house.
You can't have more than one type of animal in your enclosed area.
Allowed animals are chickens, sheep, cows, and pigs.

Do not harm villagers or existing village structures in the process.

Throw a snowball to end the episode.
"""

    def __init__(self, high_res: bool):
        super().__init__(
            name="MineRLBasaltCreateVillageAnimalPen-v0",
            demo_server_experiment_name="village_pen_animals",
            max_episode_steps=5*MINUTE,
            high_res=high_res,
            inventory=[
                dict(type="fence", quantity=64),
                dict(type="fence_gate", quantity=64),
                dict(type="carrot", quantity=1),
                dict(type="wheat_seeds", quantity=1),
                dict(type="wheat", quantity=1),
                dict(type="snowball", quantity=1),
            ],
        )

    def create_server_world_generators(self) -> List[handlers.Handler]:
        return [handlers.BiomeGenerator("plains")]

    def create_server_decorators(self) -> List[handlers.Handler]:
        return [handlers.VillageSpawnDecorator()]


class VillageMakeHouseEnvSpec(BasaltBaseEnvSpec):
    """
.. image:: ../assets/basalt/house_0_0-05.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/house_1_0-30.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/house_3_1-00.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/basalt/house_long_7-00.gif
  :scale: 100 %
  :alt:

Build a house in the style of the village without damaging the village. Give a tour of
the house and then throw a snowball to end the episode.

.. note::
  In the observation and action spaces, the following (internal Minecraft) item IDs can be
  interpreted as follows:

    - ``log#0`` is oak logs.
    - ``log#1`` is spruce logs.
    - ``log2#0`` is acacia logs.
    - ``planks#0`` is oak planks.
    - ``planks#1`` is spruce planks.
    - ``planks#4`` is acacia planks.
    - ``sandstone#0`` is cracked sandstone.
    - ``sandstone#2`` is smooth sandstone.

.. tip::
  You can find detailed information on which materials are used in each biome-specific
  village (plains, savannah, taiga, desert) here:
  https://minecraft.fandom.com/wiki/Village/Structure_(old)/Blueprints#Village_generation

"""
    def __init__(self, high_res: bool):
        super().__init__(
            name="MineRLBasaltBuildVillageHouse-v0",
            demo_server_experiment_name="village_make_house",
            max_episode_steps=12*MINUTE,
            high_res=high_res,
            inventory=MAKE_HOUSE_VILLAGE_INVENTORY,
        )

    def create_server_world_generators(self) -> List[handlers.Handler]:
        return [handlers.DefaultWorldGenerator()]

    def create_server_decorators(self) -> List[handlers.Handler]:
        return [handlers.VillageSpawnDecorator()]

    def create_observables(self):
        observables = [
            x for x in super().create_observables()
            if not isinstance(x, (
                handlers.FlatInventoryObservation,
                handlers.EquippedItemObservation,
            ))
        ]
        observables.append(
            handlers.FlatInventoryObservation(MAKE_HOUSE_VILLAGE_ITEM_IDS))
        observables.append(
            handlers.EquippedItemObservation(MAKE_HOUSE_VILLAGE_ITEM_IDS))
        return observables

    def create_actionables(self):
        actionables = [
            x for x in super().create_actionables()
            if not isinstance(x, (
                handlers.EquipAction,
            ))
        ]
        actionables.append(
            handlers.EquipAction(MAKE_HOUSE_VILLAGE_ITEM_IDS),
        )
        return actionables
