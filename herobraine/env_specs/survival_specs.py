from typing import List

import gym

import herobraine
import herobraine.hero.handlers as handlers
from herobraine.hero.mc import ALL_ITEMS, INVERSE_KEYMAP
from herobraine.env_specs.env_spec import EnvSpec

from minerl.env import spaces
from minerl.env.core import MineRLEnv, missions_dir
from collections import OrderedDict

none = ['none']
other = ['other']


ALL_ITEMS_WITHOUT_AIR = [x for x in ALL_ITEMS if not 'air' in x]
class SurvivalLimited(EnvSpec):
    def __init__(self, name='MineRLSurvivalLimited-v0'):
        self.resolution = tuple((64, 64))
        super().__init__(name, self.resolution)

    @staticmethod
    def is_from_folder(folder: str) -> bool:
        return folder == 'none'

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        return [handlers.RewardForCollectingItems({
                k: 1 for k in ALL_ITEMS_WITHOUT_AIR
            })
        ]

    def create_observables(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.POVObservation(self.resolution),
            handlers.FlatInventoryObservation(ALL_ITEMS),
            handlers.TypeObservation('mainhand', none + ALL_ITEMS + other),
            handlers.DamageObservation('mainhand'),
            handlers.MaxDamageObservation('mainhand')
        ]

    def create_actionables(self) -> List[herobraine.hero.AgentHandler]:
        actionables = [
            handlers.SingleKeyboardAction(k, v) for k,v in INVERSE_KEYMAP.items()
        ]
        actionables +=[    
            handlers.CraftItem(none + ALL_ITEMS),
            handlers.CraftItemNearby(none + ALL_ITEMS),
            handlers.SmeltItemNearby(none + ALL_ITEMS),
            handlers.PlaceBlock(none + ALL_ITEMS),
            handlers.EquipItem(none + ALL_ITEMS),
            handlers.Camera(),
        ]
        return actionables



# spec = SurvivalLimited()

# gym.register(
#     id='MineRLSurvivalLimited-v0',
#     entry_point='minerl.env:MineRLEnv',
#     kwargs={
#         'observation_space': spec.get_observation_space(),
#         'action_space': spec.get_action_space(),
#         'docstr': """
# .. image:: ../assets/treechop1.mp4.gif
#   :scale: 100 %
#   :alt: 

# .. image:: ../assets/treechop2.mp4.gif
#   :scale: 100 %
#   :alt: 

# .. image:: ../assets/treechop3.mp4.gif
#   :scale: 100 %
#   :alt: 

# .. image:: ../assets/treechop4.mp4.gif
#   :scale: 100 %
#   :alt: 
# In treechop, the agent must collect 64 `minercaft:log`. This replicates a common scenario in Minecraft, as logs are necessary to craft a large amount of items in the game, and are a key resource in Minecraft.

# The agent begins in a forest biome (near many trees) with an iron axe for cutting trees. The agent is given +1 reward for obtaining each unit of wood, and the episode terminates once the agent obtains 64 units.\n"""
#     },
#     max_episode_steps=8000,
#     reward_threshold=64.0,
# )
