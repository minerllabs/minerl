
from minerl.herobraine.hero.spaces import Box
from minerl.herobraine.hero.handlers.translation import TranslationHandler
from minerl.herobraine.hero.handler import Handler
import jinja2
from typing import List,Dict,Union
import numpy as np


class RewardHandler(TranslationHandler):
    """
    Specifies a reward handler for a task.
    These need to be attached to tasks with reinforcement learning objectives.
    All rewards need inherit from this reward handler
    #Todo: Figure out how this interplays with Hero, as rewards are summed.
    """

    def __init__(self):
        super().__init__(Box(-np.inf, np.inf, shape=()))

    def from_hero(self, obs_dict):
        """
        By default hero will include the reward in the observation.
        This is just a pass through for convenience.
        :param obs_dict:
        :return: The reward
        """
        return obs_dict["reward"]



class ConstantReward(RewardHandler):
    """
    A constant reward handler
    """

    def __init__(self, constant):
        super().__init__()
        self.constant = constant

    def from_hero(self, obs_dict):
        return self.constant

    def from_universal(self, x):
        return self.constant



# <RewardForPossessingItem sparse="true">
    # <Item amount="1" reward="1" type="log" />
    # <Item amount="1" reward="2" type="planks" />
# <RewardForPossessingItem sparse="true">

class RewardForPosessingItem(Handler):
    def to_string(self) -> str:
        return "reward_for_posessing_item"

    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<RewardForPossessingItem sparse="{{ str(sparse).lower() }}" excludeLoops="{{ str(exclude_loops).lower()}}">
                    {% for item in items %}
                    <Item amount="{{ item.amount }}" reward="{{ item.reward }}" type="{{ item.type }}" />
                    {% endfor %}
                </RewardForPossessingItem>
                """
        )

    def __init__(self, sparse : bool,  exclude_loops : bool, item_rewards : List[Dict[str, Union[str,int]]], ):
        """Creates a reward which gives rewards based on items in the 
        inventory that are provided.

        See Malmo for documentation.
        """
        self.sparse = sparse
        self.exclude_loops = exclude_loops
        self.items = item_rewards
        # Assert all items have the appropriate fields for the XML template.
        for item in self.items:
            assert set(item.keys()) == {"amount", "reward", "type"}


# <RewardForMissionEnd>
#     <Reward description="out_of_time" reward="0" />
# </RewardForMissionEnd>
class RewardForMissionEnd(Handler):
    def to_string(self) -> str:
        return "reward_for_mission_end"

    def xml_element(self) -> jinja2.Template:
        return jinja2.Template(
            """<RewardForMissionEnd>
                    <Reward description="{{ description }}" reward="{{ reward }}" />
                </RewardForMissionEnd>"""
        )
    
    def __init__(self, reward : int, description :str = "out_of_time"):
        """Creates a reward which is awarded when a mission ends."""
        self.reward = reward
        self.description = description


#  <RewardForTouchingBlockType>
#     <Block reward="100.0" type="diamond_block" behaviour="onceOnly"/>
#     <Block reward="189.0" type="diamond_block" behaviour="onceOnly"/>
# </RewardForTouchingBlockType>
class RewardForTouchingBlockType(Handler):
    def to_string(self) -> str:
        return "reward_for_touching_block_type"

    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<RewardForTouchingBlockType>
                    {% for block in blocks %}
                    <Block reward="{{ block.reward }}" type="{{ block.type }}" behaviour="{{ block.behaviour }}" />
                    {% endfor %}
                </RewardForTouchingBlockType>"""
        )

    def __init__(self, blocks : List[Dict[str, Union[str, int]]]):
        """Creates a reward which is awarded when the player touches a block."""
        self.blocks = blocks
        # Assert all blocks have the appropriate fields for the XML template.
        for block in self.blocks:
            assert set(block.keys()) == {"reward", "type", "behaviour"}


# <RewardForDistanceTraveledToCompassTarget rewardPerBlock="1" density="PER_TICK"/>
class RewardForDistanceTraveledToCompassTarget(Handler):
    def to_string(self) -> str:
        return "reward_for_distance_traveled_to_compass_target"

    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<RewardForDistanceTraveledToCompassTarget rewardPerBlock="{{ rewardPerBlock }}" density="{{ density }}"/>"""
        )

    def __init__(self, reward_per_block : int, density : str):
        """Creates a reward which is awarded when the player reaches a certain distance from a target."""
        self.reward_per_block = reward_per_block
        self.density = density


# Reward for crafting item.

class RewardForCraftingItem(RewardHandler):
    """
    Reward a player for crafting an item - currently crafting is tracked via slot clicks
    """
    item_dict = {}

    def __init__(self, item_dict):
        """
        Adds a reward for collecting a certain set of items.
        :param item_name: The name
        :param reward: The reward
        :param args: So on and so forth.
        """
        super().__init__()

        self.reward_dict = item_dict
        self.prev_container = None
        self.skip_next = False

    def add_to_mission_xml(self, etree: Element, namespace: str):
        """
        Adds the following to the mission xml
           <RewardForCollectingItem>
            <Item  reward="1" type="log" />
          </RewardForCollectingItem>
        :param etree:
        :param namespace:
        :return:
        """
        child = Element("RewardForCraftingItem")
        for item, reward in self.reward_dict.items():
            item_eml = Element("Item")
            item_eml.set("reward", str(reward))
            item_eml.set("type", item)
            child.append(item_eml)

        for agenthandlers in etree.iter('{{{}}}AgentHandlers'.format(namespace)):
            agenthandlers.append(child)
        super().add_to_mission_xml(etree, namespace)

    def from_universal(self, obs):
        try:
            if self.prev_container is not None and obs['slots']['gui']['type'] != self.prev_container:
                self.skip_next = True
                return 0
            elif self.skip_next:
                self.skip_next = False
                return 0
            elif 'diff' in obs and 'crafted' in obs['diff']:
                for crafted in obs['diff']['crafted']:
                    item_name = strip_of_prefix(crafted['name'])
                    if item_name in self.item_dict:
                        return self.item_dict[item_name]
            return 0
        finally:
            try:
                self.prev_container = obs['slots']['gui']['type']
            except KeyError:
                self.prev_container = None

    def reset(self):
        self.skip_next = False
        self.prev_container = None