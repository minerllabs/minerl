from minerl.herobraine.env_specs.simple_env_spec import SimpleEnvSpec
from minerl.herobraine.hero import handlers, AgentHandler
from typing import List
from gym import spaces

none = 'none'


def snake_to_camel(word):
    import re
    return ''.join(x.capitalize() or '_' for x in word.split('_'))


class Obtain(SimpleEnvSpec):
    def __init__(self,
                 target_item,
                 dense,
                 reward_schedule,
                 max_episode_steps=6000):
        self.target_item = target_item
        self.dense = dense
        suffix = snake_to_camel(self.target_item)
        dense_suffix = "Dense" if self.dense else ""
        self.reward_schedule = reward_schedule
        super().__init__(
            name="MineRLObtain{}{}-v0".format(suffix, dense_suffix),
            xml="obtain{}{}.xml".format(suffix, dense_suffix),
            max_episode_steps=max_episode_steps,
        )

    def is_from_folder(self, folder: str):
        return folder == 'o_{}'.format(self.target_item)

    def get_docstring(self):
        return ""

    def create_mission_handlers(self) -> List[AgentHandler]:
        reward_handler = (
            handlers.RewardForCollectingItems if self.dense
            else handlers.RewardForCollectingItemsOnce)

        return [
            reward_handler(self.reward_schedule if self.reward_schedule else {self.target_item: 1})
        ]

    def determine_success_from_rewards(self, rewards: list) -> bool:
        # TODO: Convert this to finish handlers.
        rewards = set(rewards)
        allow_missing_ratio = 0.1
        max_missing = round(len(self.reward_schedule) * allow_missing_ratio)
        return len(rewards.intersection(self.reward_schedule.values())) \
            >= len(self.reward_schedule.values()) - max_missing

    def create_observables(self) -> List[AgentHandler]:
        # TODO: Parameterize these observations.
        return super().create_observables() + [
            handlers.FlatInventoryObservation([
                'dirt',
                'coal',
                'torch',
                'log',
                'planks',
                'stick',
                'crafting_table',
                'wooden_axe',
                'wooden_pickaxe',
                'stone',
                'cobblestone',
                'furnace',
                'stone_axe',
                'stone_pickaxe',
                'iron_ore',
                'iron_ingot',
                'iron_axe',
                'iron_pickaxe'
            ]),
            handlers.DamageObservation('mainhand'),
            handlers.MaxDamageObservation('mainhand'),
            handlers.TypeObservation('mainhand',
                                     ['none', 'air', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe',
                                      'iron_axe', 'iron_pickaxe', 'other']),
        ]

    def create_actionables(self):
        return super().create_actionables() + [
            handlers.PlaceBlock(['none', 'dirt', 'stone', 'cobblestone', 'crafting_table', 'furnace', 'torch']),
            handlers.EquipItem(['none', 'air', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe',
                                'iron_pickaxe']),
            handlers.CraftItem(['none', 'torch', 'stick', 'planks', 'crafting_table']),
            handlers.CraftItemNearby(
                ['none', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe', 'iron_pickaxe',
                 'furnace']),
            handlers.SmeltItemNearby(['none', 'iron_ingot', 'coal']),
        ]


class ObtainDiamond(Obtain):
    def __init__(self, dense):
        super(ObtainDiamond, self).__init__(
            target_item='diamond',
            dense=dense,
            reward_schedule={
                "log": 1,
                "planks": 2,
                "stick": 4,
                "crafting_table": 4,
                "wooden_pickaxe": 8,
                "cobblestone": 16,
                "furnace": 32,
                "stone_pickaxe": 32,
                "iron_ore": 64,
                "iron_ingot": 128,
                "iron_pickaxe": 256,
                "diamond": 1024
            },
            max_episode_steps=18000
        )

    def is_from_folder(self, folder: str) -> bool:
        return folder == 'o_dia'

    def get_docstring(self):
        return """
.. image:: ../assets/odia1.mp4.gif
  :scale: 100 %
  :alt: 

.. image:: ../assets/odia2.mp4.gif
  :scale: 100 %
  :alt: 

.. image:: ../assets/odia3.mp4.gif
  :scale: 100 %
  :alt: 

.. image:: ../assets/odia4.mp4.gif
  :scale: 100 %
  :alt: 

In this environment the agent is required to obtain a diamond.
The agent begins in a random starting location on a random survival map without any items, matching the normal starting conditions for human players in Minecraft.
The agent is given access to a selected summary of its inventory and GUI free
crafting, smelting, and inventory management actions.


During an episode the agent is rewarded **every** time it obtains an item
in the requisite item hierarchy to obtaining a diamond. The rewards for each
item are given here::

    <Item reward="1" type="log" />
    <Item reward="2" type="planks" />
    <Item reward="4" type="stick" />
    <Item reward="4" type="crafting_table" />
    <Item reward="8" type="wooden_pickaxe" />
    <Item reward="16" type="cobblestone" />
    <Item reward="32" type="furnace" />
    <Item reward="32" type="stone_pickaxe" />
    <Item reward="64" type="iron_ore" />
    <Item reward="128" type="iron_ingot" />
    <Item reward="256" type="iron_pickaxe" />
    <Item reward="1024" type="diamond" />

\n"""


class ObtainIronPickaxe(Obtain):
    def __init__(self, dense):
        super(ObtainIronPickaxe, self).__init__(
            target_item='iron_pickaxe',
            dense=dense,
            reward_schedule={
                "log": 1,
                "planks": 2,
                "stick": 4,
                "crafting_table": 4,
                "wooden_pickaxe": 8,
                "cobblestone": 16,
                "furnace": 32,
                "stone_pickaxe": 32,
                "iron_ore": 64,
                "iron_ingot": 128,
                "iron_pickaxe": 256,
            }
        )

    def is_from_folder(self, folder: str) -> bool:
        return folder == 'o_iron'

    def get_docstring(self):
        return """
.. image:: ../assets/orion1.mp4.gif
  :scale: 100 %
  :alt: 

.. image:: ../assets/orion2.mp4.gif
  :scale: 100 %
  :alt: 

.. image:: ../assets/orion3.mp4.gif
  :scale: 100 %
  :alt: 

.. image:: ../assets/orion4.mp4.gif
  :scale: 100 %
  :alt: 
In this environment the agent is required to obtain an iron pickaxe. The agent begins in a random starting location, on a random survival map, without any items, matching the normal starting conditions for human players in Minecraft.
The agent is given access to a selected view of its inventory and GUI free
crafting, smelting, and inventory management actions.


During an episode **the agent is rewarded only once per item the first time it obtains that item
in the requisite item hierarchy for obtaining an iron pickaxe.** The reward for each
item is given here::
    <Item amount="1" reward="1" type="log" />
    <Item amount="1" reward="2" type="planks" />
    <Item amount="1" reward="4" type="stick" />
    <Item amount="1" reward="4" type="crafting_table" />
    <Item amount="1" reward="8" type="wooden_pickaxe" />
    <Item amount="1" reward="16" type="cobblestone" />
    <Item amount="1" reward="32" type="furnace" />
    <Item amount="1" reward="32" type="stone_pickaxe" />
    <Item amount="1" reward="64" type="iron_ore" />
    <Item amount="1" reward="128" type="iron_ingot" />
    <Item amount="1" reward="256" type="iron_pickaxe" />

\n"""


class ObtainDiamondSurvival(ObtainDiamond):
    def __init__(self, dense):
        super(ObtainDiamondSurvival, self).__init__(dense)
        self.name = "MineRLObtainDiamondSurvival-v0"

    def is_from_folder(self, folder: str):
        return folder == 'none'


class ObtainDiamondDebug(ObtainDiamond):
    def __init__(self, dense):
        super().__init__(dense=dense)

        self.name = "MineRLObtainTest{}-v0".format('' if not dense else 'Dense')
        self.xml = "obtainDebug{}.xml".format('' if not dense else 'Dense')

    def create_actionables(self):
        return SimpleEnvSpec.create_actionables(self) + [
            handlers.PlaceBlock(
                ['none', 'dirt', 'log', 'log2', 'stone', 'cobblestone', 'crafting_table', 'furnace', 'torch',
                 'diamond_ore']),
            handlers.EquipItem(
                ['none', 'red_flower', 'air', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe',
                 'iron_pickaxe']),
            handlers.CraftItem(['none', 'torch', 'stick', 'planks', 'crafting_table']),
            handlers.CraftItemNearby(
                ['none', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe', 'iron_pickaxe',
                 'furnace']),
            handlers.SmeltItemNearby(['none', 'iron_ingot', 'coal']),
        ]

    def is_from_folder(self, folder: str):
        return False

    def get_docstring(self):
        return """This environment intended for continuous integration testing only!!"""
