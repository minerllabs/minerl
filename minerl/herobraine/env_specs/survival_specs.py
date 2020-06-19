from typing import List

import gym

import minerl.herobraine
import minerl.herobraine.hero.handlers as handlers
from minerl.herobraine.hero.mc import ALL_ITEMS, INVERSE_KEYMAP
from minerl.herobraine.env_spec import EnvSpec

from collections import OrderedDict

none = ['none']
other = ['other']


ALL_ITEMS_WITHOUT_AIR = [x for x in ALL_ITEMS if not 'air' in x]
class SurvivalLimited(EnvSpec):
    def __init__(self, name='MineRLSurvivalLimited-v0'):
        self.resolution = tuple((64, 64))
        super().__init__(name, self.resolution)

    def is_from_folder(folder: str) -> bool:
        return folder == 'none'

    def create_mission_handlers(self) -> List[minerl.herobraine.hero.AgentHandler]:
        return [handlers.RewardForCollectingItems({
                k: 1 for k in ALL_ITEMS_WITHOUT_AIR
            })
        ]

    def create_observables(self) -> List[minerl.herobraine.hero.AgentHandler]:
        return [
            handlers.POVObservation(self.resolution),
            handlers.FlatInventoryObservation(ALL_ITEMS),
            handlers.TypeObservation('mainhand', none + ALL_ITEMS + other),
            handlers.DamageObservation('mainhand'),
            handlers.MaxDamageObservation('mainhand')
        ]

    def create_actionables(self) -> List[minerl.herobraine.hero.AgentHandler]:
        actionables = [
            handlers.KeyboardAction(k, v) for k,v in INVERSE_KEYMAP.items()
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

