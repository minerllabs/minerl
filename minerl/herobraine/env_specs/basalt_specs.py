from typing import List, Optional, Sequence

import gym

from minerl.env import _fake, _singleagent
from minerl.herobraine import wrappers
from minerl.herobraine.env_spec import EnvSpec
from minerl.herobraine.env_specs import simple_embodiment
from minerl.herobraine.hero import handlers, mc

from minerl.herobraine.env_specs.human_controls import HumanControlEnvSpec


MAKE_HOUSE_VILLAGE_INVENTORY = [
    dict(type="stone_pickaxe", quantity=1),
    dict(type="stone_axe", quantity=1),
    dict(type="cobblestone", quantity=64),
    dict(type="oak_log", quantity=64),
    dict(type="glass_pane", quantity=64),
    dict(type="torch", quantity=64),
    dict(type="dirt", quantity=64),
    dict(type="grass_block", quantity=64),
    dict(type="poppy", quantity=64),
    dict(type="spruce_log", quantity=64),
    dict(type="acacia_log", quantity=64),
    dict(type="jungle_log", quantity=64),
    dict(type="sand", quantity=64),
    dict(type="sandstone", quantity=64),
    dict(type="smooth_sandstone", quantity=64),
    dict(type="terracotta", quantity=64),
    dict(type="packed_ice", quantity=64),
    dict(type="snow_block", quantity=64),
    dict(type="cobweb", quantity=64),
    dict(type="white_wool", quantity=64),
    dict(type="black_dye", quantity=64),
    dict(type="blue_dye", quantity=64),
    dict(type="brown_dye", quantity=64),
    dict(type="green_dye", quantity=64),
    dict(type="red_dye", quantity=64),
    dict(type="white_dye", quantity=64),
    dict(type="yellow_dye", quantity=64),
    dict(type="flower_pot", quantity=64),
    dict(type="cactus", quantity=64),
    dict(type="lantern", quantity=64),
]

class BasaltTimeoutWrapper(gym.Wrapper):
    """Timeout wrapper specifically crafted for the BASALT environments"""
    def __init__(self, env):
        super().__init__(env)
        self.timeout = self.env.task.max_episode_steps
        self.num_steps = 0

    def reset(self):
        self.timeout = self.env.task.max_episode_steps
        self.num_steps = 0
        return super().reset()

    def step(self, action):
        observation, reward, done, info = super().step(action)
        self.num_steps += 1
        if self.num_steps >= self.timeout:
            done = True
        return observation, reward, done, info


class DoneOnESCWrapper(gym.Wrapper):
    """
    Use the "ESC" action of the MineRL 1.0.0 to end
    an episode (if 1, step will return done=True)
    """
    def __init__(self, env):
        super().__init__(env)
        self.episode_over = False

    def reset(self):
        self.episode_over = False
        return self.env.reset()

    def step(self, action):
        if self.episode_over:
            raise RuntimeError("Expected `reset` after episode terminated, not `step`.")
        observation, reward, done, info = self.env.step(action)
        done = done or bool(action["ESC"])
        self.episode_over = done
        return observation, reward, done, info


def _basalt_gym_entrypoint(
        env_spec: "BasaltBaseEnvSpec",
        fake: bool = False,
) -> _singleagent._SingleAgentEnv:
    """Used as entrypoint for `gym.make`."""
    if fake:
        env = _fake._FakeSingleAgentEnv(env_spec=env_spec)
    else:
        env = _singleagent._SingleAgentEnv(env_spec=env_spec)

    env = BasaltTimeoutWrapper(env)
    env = DoneOnESCWrapper(env)
    return env


BASALT_GYM_ENTRY_POINT = "minerl.herobraine.env_specs.basalt_specs:_basalt_gym_entrypoint"


class BasaltBaseEnvSpec(HumanControlEnvSpec):

    LOW_RES_SIZE = 64
    HIGH_RES_SIZE = 1024

    def __init__(
            self,
            name,
            demo_server_experiment_name,
            max_episode_steps=2400,
            inventory: Sequence[dict] = (),
            preferred_spawn_biome: str = "plains"
    ):
        self.inventory = inventory  # Used by minerl.util.docs to construct Sphinx docs.
        self.preferred_spawn_biome = preferred_spawn_biome
        self.demo_server_experiment_name = demo_server_experiment_name
        super().__init__(
            name=name,
            max_episode_steps=max_episode_steps,
            # Hardcoded variables to match the pretrained models
            fov_range=[70, 70],
            resolution=[640, 360],
            gamma_range=[2, 2],
            guiscale_range=[1, 1],
            cursor_size_range=[16.0, 16.0]
        )

    def is_from_folder(self, folder: str) -> bool:
        # Implements abstractmethod.
        return folder == self.demo_server_experiment_name

    def _entry_point(self, fake: bool) -> str:
        # Don't need to inspect `fake` argument here because it is also passed to the
        # entrypoint function.
        return BASALT_GYM_ENTRY_POINT

    def create_observables(self):
        # Only POV
        obs_handler_pov = handlers.POVObservation(self.resolution)
        return [obs_handler_pov]

    def create_agent_start(self) -> List[handlers.Handler]:
        return super().create_agent_start() + [
            handlers.SimpleInventoryAgentStart(self.inventory),
            handlers.PreferredSpawnBiome(self.preferred_spawn_biome),
            handlers.DoneOnDeath()
        ]

    def create_agent_handlers(self) -> List[handlers.Handler]:
        return []

    def create_server_world_generators(self) -> List[handlers.Handler]:
        # TODO the original biome forced is not implemented yet. Use this for now.
        return [handlers.DefaultWorldGenerator(force_reset=True)]

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
        # TODO Clean up snowball stuff (not used anymore)
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

After spawning in a plains biome, explore and find a cave. When inside a cave, end
the episode by setting the "ESC" action to 1.

You are not allowed to dig down from the surface to find a cave.
"""

    def __init__(self):
        super().__init__(
            name="MineRLBasaltFindCave-v0",
            demo_server_experiment_name="findcaves",
            max_episode_steps=3*MINUTE,
            preferred_spawn_biome="plains",
            inventory=[],
        )


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

After spawning in an extreme hills biome, use your waterbucket to make a beautiful waterfall.
Then take an aesthetic "picture" of it by moving to a good location, positioning
player's camera to have a nice view of the waterfall, and ending the episode by
setting "ESC" action to 1.
"""

    def __init__(self):
        super().__init__(
            name="MineRLBasaltMakeWaterfall-v0",
            demo_server_experiment_name="waterfall",
            max_episode_steps=5*MINUTE,
            preferred_spawn_biome="extreme_hills",
            inventory=[
                dict(type="water_bucket", quantity=1),
                dict(type="cobblestone", quantity=20),
                dict(type="stone_shovel", quantity=1),
                dict(type="stone_pickaxe", quantity=1),
            ],
        )


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

After spawning in a village, build an animal pen next to one of the houses in a village.
Use your fence posts to build one animal pen that contains at least two of the same animal.
(You are only allowed to pen chickens, cows, pigs, or sheep.)
There should be at least one gate that allows players to enter and exit easily.
The animal pen should not contain more than one type of animal.
(You may kill any extra types of animals that accidentally got into the pen.)

Do not harm villagers or existing village structures in the process.

Send 1 for "ESC" key to end the episode.
"""

    def __init__(self):
        super().__init__(
            name="MineRLBasaltCreateVillageAnimalPen-v0",
            demo_server_experiment_name="village_pen_animals",
            max_episode_steps=5*MINUTE,
            preferred_spawn_biome="plains",
            inventory=[
                dict(type="oak_fence", quantity=64),
                dict(type="oak_fence_gate", quantity=64),
                dict(type="carrot", quantity=1),
                dict(type="wheat_seeds", quantity=1),
                dict(type="wheat", quantity=1),
            ],
        )

    def create_agent_start(self) -> List[handlers.Handler]:
        return super().create_agent_start() + [
            handlers.SpawnInVillage()
        ]


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

Build a house in the style of the village without damaging the village. It
should be in an appropriate location  (e.g. next to the path through the village)
Then, give a brief tour of the house (i.e. spin around slowly such that all of the
walls and the roof are visible).
Finally, end the episode by setting the "ESC" action to 1.


.. tip::
  You can find detailed information on which materials are used in each biome-specific
  village (plains, savannah, taiga, desert) here:
  https://minecraft.wiki/w/Village/Structure/Blueprints
"""
    def __init__(self):
        super().__init__(
            name="MineRLBasaltBuildVillageHouse-v0",
            demo_server_experiment_name="village_make_house",
            max_episode_steps=12*MINUTE,
            preferred_spawn_biome="plains",
            inventory=MAKE_HOUSE_VILLAGE_INVENTORY,
        )

    def create_agent_start(self) -> List[handlers.Handler]:
        return super().create_agent_start() + [
            handlers.SpawnInVillage()
        ]
