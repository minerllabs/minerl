from abc import ABC
from xml.etree.ElementTree import Element

import gym
import numpy as np

from minerl.herobraine.hero import AgentHandler


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

    def __init__(self, item_dict):
        """
        Adds a reward for collecting a certain set of items.
        :param item_name: The name
        :param reward: The reward
        :param args: So on and so forth.
        """
        super().__init__()
        self.reward_dict = item_dict

    def from_universal(self, x):
        total_reward = 0
        if 'diff' in x and 'changes' in x['diff']:
            for change_json in x['diff']['changes']:
                item_name = strip_of_prefix(change_json['item'])
                if item_name == 'log2':
                    item_name = 'log'
                if item_name in self.reward_dict and 'quantity_change' in change_json:
                    if change_json['quantity_change'] > 0:
                        total_reward += change_json['quantity_change'] * self.reward_dict[item_name]
        return total_reward


class RewardForCollectingItemsOnce(RewardHandler):
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
        self.seen_dict = dict()
        self.reward_dict = item_dict

    def from_universal(self, x):
        total_reward = 0
        if 'diff' in x and 'changes' in x['diff']:
            for change_json in x['diff']['changes']:
                item_name = strip_of_prefix(change_json['item'])
                if item_name == 'log2':
                    item_name = 'log'
                if item_name in self.reward_dict and 'quantity_change' in change_json and item_name not in self.seen_dict:
                    if change_json['quantity_change'] > 0:
                        total_reward += self.reward_dict[item_name]
                        self.seen_dict[item_name] = True
        return total_reward

    def reset(self):
        # print(self.seen_dict.keys())
        self.seen_dict = dict()


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


class RewardForTouchingBlock(RewardHandler):
    """
    The standard malmo reward for contacting a specific block.
    """

    def __init__(self, block_dict, behavior='onceOnly', **args):
        """
        Adds a reward for touching specific blocks either once or every touch
        :param block_name: The name
        :param reward: The reward
        :param behavior: The desired behavior choice of "onceOnly" or TODO fill-in
        :param args: So on and so forth.
        """
        super().__init__()
        self.fired = False
        self.reward_dict = block_dict

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
        if 'touched_blocks' in obs and not self.fired:
            for block in obs['touched_blocks']:
                if 'minecraft:diamond_block' in block['name']:
                    self.fired = True
                    return 100
        return 0

    def reset(self):
        self.fired = False


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


class RewardForWalkingTwardsTarget(RewardHandler):
    """
    Custom reward for approaching a compass location
    """

    def __init__(self, reward_per_block=1, reward_schedule='PER_TICK', **args):
        """
        Adds a reward for touching specific blocks either once or every touch
        :param reward_per_block: The reward for each unit traveled twards compass target
        :param reward_schedule: The distribution of rewards, one of {PER_TICK, PER_TICK_ACCUMULATED, MISSION_END}
        :param args: So on and so forth.
        """
        super().__init__()

        self.reward_per_block = reward_per_block
        self.reward_schedule = reward_schedule
        self._prev_delta = None

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
            try:
                target = obs['compass']['target']
                target_pos = np.array([target["x"], target["y"], target["z"]])
                position = obs['compass']['position']
                cur_pos = np.array([position["x"], position["y"], position["z"]])
                delta = np.linalg.norm(target_pos - cur_pos)
                if not self._prev_delta:
                    return 0
                else:
                    return self._prev_delta - delta
            finally:
                self._prev_delta = delta

    def reset(self):
        self._prev_delta = None
