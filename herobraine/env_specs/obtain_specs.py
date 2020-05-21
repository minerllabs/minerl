from herobraine.env_specs.simple_env_spec import SimpleEnvSpec
from herobraine.hero import handlers




class Obtain(SimpleEnvSpec):
    def __init__(self, target_item, dense, reward_schedule):
        self.target_item = target_item
        self.dense = dense
        suffix = snake_to_camel(self.target_item)
        dense_suffix = "Dense" if self.dense else ""
        self.reward_schedule = reward_schedule
        super().__init__(
            name=f"MineRLObtain{suffix}{dense_suffix}-v0",
            xml=f"obtain{suffix}.xml",
            max_episode_steps=6000,
        )

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        reward_handler = (
            handlers.RewardForCollectingItems if self.dense 
            else handlers.RewardForCollectingItemsOnce)
        
        return [
            reward_handler(self.reward_schedule)
        ]

def snake_to_camel(word):
        import re
        return ''.join(x.capitalize() or '_' for x in word.split('_'))



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
            }
        )

    def is_from_folder(self, folder: str) -> bool:
        return folder == 'o_dia'

    def get_docstring(self):
        return f"""
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
in the requisite item hierarchy to obtaining a {target_item}. The rewards for each
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