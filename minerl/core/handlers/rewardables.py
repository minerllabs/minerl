from abc import ABC
from xml.etree.ElementTree import Element

import gym
import numpy as np

from herobraine.hero import AgentHandler

def strip_of_prefix(minecraft_name):
    # Names in minecraft start with 'minecraft:', like:
    # 'minecraft:log', or 'minecraft:cobblestone'
    if minecraft_name.startswith('minecraft:'):
        return minecraft_name[len('minecraft:'):]
    return minecraft_name

class RewardHandler(AgentHandler, ABC):
    """
    Specifies a reward handler for a task.
    These need to be attached to tasks with reinforcement learning objectives.
    All rewards need inherit from this reward handler
    #Todo: Figure out how this interplays with Hero, as rewards are summed.
    """
    def __init__(self):
        super().__init__(gym.spaces.Box(-np.inf, np.inf, [1]))

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


class RewardForCollectingItems(RewardHandler):
    """
    The standard malmo reward for collecting item.
    """

    def __init__(self, item_name, reward, **args):
        """
        Adds a reward for collecting a certain set of items.
        :param item_name: The name
        :param reward: The reward
        :param args: So on and so forth.
        """
        super().__init__()

        item_dict = {
            item_name: reward
        }
        itemreward = []
        for a in args:
            if len(itemreward) == 2:
                item_dict[itemreward[0]] = itemreward[1]
                itemreward = []
            itemreward.append(a)
        self.reward_dict = item_dict


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
        child = Element("RewardForCollectingItem")
        for item,reward in self.reward_dict.items():
            item_eml = Element("Item")
            item_eml.set("reward", str(reward))
            item_eml.set("type", item)
            child.append(item_eml)

        for agenthandlers in etree.iter('{{{}}}AgentHandlers'.format(namespace)):
            agenthandlers.append(child)
        super().add_to_mission_xml(etree, namespace)

    def from_universal(self, x):
        total_reward = 0
        if 'inventory' in x and 'changes' in x['inventory']:
            for change_json in x['inventory']['changes']:
                item_name = strip_of_prefix(change_json['item'])
                if item_name in self.reward_dict and 'quantity_change' in change_json:
                    total_reward += change_json['quantity_change'] * self.reward_dict[item_name]
        return total_reward

class RewardForCollectingItemsDict(RewardHandler):
    """
    The standard malmo reward for collecting item.
    """

    def __init__(self, item_dict):
        """
        Adds a reward for collecting a certain set of items.
        :param item_name: The name
        :param reward: The reward
        :param args: So on and so forth.
        """
        super().__init__()
        self.reward_dict = item_dict

class RewardForCraftingItem(RewardHandler):
    """
    Reward a player for crafting an item - currently crafting is tracked via slot clicks
    """
    item_dict = {}

    def __init__(self, item_name, reward, **args):
        """
        Adds a reward for collecting a certain set of items.
        :param item_name: The name
        :param reward: The reward
        :param args: So on and so forth.
        """
        super().__init__()

        item_dict = {
            item_name: reward
        }
        itemreward = []
        for a in args:
            if len(itemreward) == 2:
                item_dict[itemreward[0]] = itemreward[1]
                itemreward = []
            itemreward.append(a)
        self.reward_dict = item_dict

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
        for item,reward in self.reward_dict.items():
            item_eml = Element("Item")
            item_eml.set("reward", str(reward))
            item_eml.set("type", item)
            child.append(item_eml)

        for agenthandlers in etree.iter('{{{}}}AgentHandlers'.format(namespace)):
            agenthandlers.append(child)
        super().add_to_mission_xml(etree, namespace)

    def from_universal(self, obs):
        if 'inventory' in obs and 'crafted' in obs['inventory']:
            for crafted in obs['inventory']['crafted']:
                item_name = strip_of_prefix(crafted['name'])
                if item_name in self.item_dict:
                    return self.item_dict[item_name]
        return 0

class RewardForTouchingBlock(RewardHandler):
    """
    The standard malmo reward for contacting a specific block.
    """

    def __init__(self, block_name, reward, behavior, **args):
        """
        Adds a reward for touching specific blocks either once or every touch
        :param block_name: The name
        :param reward: The reward
        :param behavior: The desired behavior choice of "onceOnly" or TODO fill-in
        :param args: So on and so forth.
        """
        super().__init__()

        item_dict = {
            block_name: (reward, behavior)
        }
        item_reward = []
        for a in args:
            if len(item_reward) == 3:
                item_dict[item_reward[0]] = (item_reward[1], item_reward[2])
                item_reward = []
            item_reward.append(a)
        self.reward_dict = item_dict

    def add_to_mission_xml(self, etree: Element, namespace: str):
        """
        Adds the following to the mission xml
           <RewardForTouchingBlockType>
                <Block reward="100.0" type="diamond_block" behaviour="onceOnly"/>
            </RewardForTouchingBlockType>
        :param etree:
        :param namespace:
        :return:
        """
        child = Element("RewardForTouchingBlockType")
        for item, (reward, behavior) in self.reward_dict.items():
            item_eml = Element("Block")
            item_eml.set("reward", str(reward))
            item_eml.set("type", item)
            # DO NOT CHANGE THIS
            # "behavior is mispelled as "behaviour" in our malmo
            item_eml.set("behaviour", behavior)
            child.append(item_eml)

        for agenthandlers in etree.iter('{{{}}}AgentHandlers'.format(namespace)):
            agenthandlers.append(child)
        super().add_to_mission_xml(etree, namespace)

    def from_universal(self, obs):
        if 'touched_blocks' in obs:
            for block in obs['touched_blocks']:
                if 'minecraft:diamond_block' in block['name']:
                    return 100
        return 0

class NavigateTargetReward(RewardHandler):
    """
    The standard malmo reward for contacting a specific block.
    """
    behavior = None
    reward_dict = None

    def __init__(self):
        super().__init__()

    def add_to_mission_xml(self, etree: Element, namespace: str):
        pass

    def from_universal(self, obs):
        if 'navigateHelper' in obs:
            if 'minecraft:diamond_block' == obs['navigateHelper']:
                return 100
        return 0

class RewardForWalkingTowardsTarget(RewardHandler):
    """
    Custom reward for approaching a compass location
    """

    def __init__(self, reward_per_block=1, reward_schedule='PER_TICK', **args):
        """
        Adds a reward for touching specific blocks either once or every touch
        :param reward_per_block: The reward for each unit traveled towards compass target
        :param reward_schedule: The distribution of rewards, one of {PER_TICK, PER_TICK_ACCUMULATED, MISSION_END}
        :param args: So on and so forth.
        """
        super().__init__()

        self.reward_per_block = reward_per_block
        self.reward_schedule = reward_schedule

    def add_to_mission_xml(self, etree: Element, namespace: str):
        """
        Example addition to the mission xml
           <RewardForDistanceTraveledToCompassTarget>
                <RewardProducerAttributes reward="100.0" type="diamond_block" behaviour="onceOnly"/>
           </RewardForDistanceTraveledToCompassTarget>
        :param etree:
        :param namespace:
        :return:
        """
        elem = Element("RewardForDistanceTraveledToCompassTarget")
        elem.set("density", self.reward_schedule)
        elem.set("rewardPerBlock", str(self.reward_per_block))

        for agenthandlers in etree.iter('{{{}}}AgentHandlers'.format(namespace)):
            agenthandlers.append(elem)
        super().add_to_mission_xml(etree, namespace)

    def from_universal(self, obs):
        if 'compass' in obs and 'deltaDistance' in obs['compass']:
            return obs['compass']['deltaDistance']
