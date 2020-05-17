from typing import List

import herobraine
import herobraine.hero.handlers as handlers
from herobraine.hero.mc import ALL_ITEMS
from herobraine.env_specs.env_spec import EnvSpec

from minerl.env import spaces
from minerl.env.core import MineRLEnv, missions_dir
from collections import OrderedDict


class SurvivalLimited(EnvSpec):
    def __init__(self, name='MineRLSurvivalLimited-v0'):
        self.resolution = tuple((64, 64))
        super().__init__(name, self.resolution)

    @staticmethod
    def is_from_folder(folder: str) -> bool:
        return folder == 'none'

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        return []

    def create_observables(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.POVObservation(self.resolution),
            handlers.FlatInventoryObservation(ALL_ITEMS)
        ]

    def create_actionables(self) -> List[herobraine.hero.AgentHandler]:
        actionables = [
            handlers.SingleKeyboardAction("forward", "W"),
            handlers.SingleKeyboardAction("back", "S"),
            handlers.SingleKeyboardAction("left", "A"),
            handlers.SingleKeyboardAction("right", "D"),
            handlers.KeyboardAction("strafe", "A", "D"),
            handlers.KeyboardAction("jump", "SPACE"),
            handlers.KeyboardAction("crouch", "SHIFT"),
            handlers.KeyboardAction("attack", "BUTTON0"),
            handlers.KeyboardAction("use", "BUTTON1"),
            handlers.CraftItem([ALL_ITEMS]),
            handlers.CraftItemNearby([ALL_ITEMS]),
            handlers.SmeltItemNearby([ALL_ITEMS]),
            handlers.PlaceBlock([ALL_ITEMS]),
            handlers.Camera()
        ]
        return actionables

spec = SurvivalLimited()



register(
    id='MineRLSurvivalLimited-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'observation_space': spaces.Dict(spaces={
            o.to_string(): o.space for o in spec.create_observables()
        }),
        'action_space': spaces.Dict(spaces={
            a.to_string(): a.space for a in spec.create_actionables(()
            # "forward": spaces.Discrete(2), 
            # "back": spaces.Discrete(2), 
            # "left": spaces.Discrete(2), 
            # "right": spaces.Discrete(2), 
            # "jump": spaces.Discrete(2), 
            # "sneak": spaces.Discrete(2), 
            # "sprint": spaces.Discrete(2), 
            # "attack": spaces.Discrete(2),
            # "camera": spaces.Box(low=-180, high=180, shape=(2,), dtype=np.float32),
        }),
        'docstr': """
.. image:: ../assets/treechop1.mp4.gif
  :scale: 100 %
  :alt: 

.. image:: ../assets/treechop2.mp4.gif
  :scale: 100 %
  :alt: 

.. image:: ../assets/treechop3.mp4.gif
  :scale: 100 %
  :alt: 

.. image:: ../assets/treechop4.mp4.gif
  :scale: 100 %
  :alt: 
In treechop, the agent must collect 64 `minercaft:log`. This replicates a common scenario in Minecraft, as logs are necessary to craft a large amount of items in the game, and are a key resource in Minecraft.

The agent begins in a forest biome (near many trees) with an iron axe for cutting trees. The agent is given +1 reward for obtaining each unit of wood, and the episode terminates once the agent obtains 64 units.\n"""
    },
    max_episode_steps=8000,
    reward_threshold=64.0,
)
