"""
These handlers modify what things the agent gets rewarded for. 

When used to create a Gym environment, they should be passed to :code:`create_rewardables`
"""
# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import abc
from minerl.herobraine.hero.mc import strip_item_prefix
from minerl.herobraine.hero.spaces import Box
from minerl.herobraine.hero.handlers.translation import TranslationHandler
from minerl.herobraine.hero.handler import Handler
import jinja2
from typing import List, Dict, Union
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
    """A constant reward handler"""

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
class _RewardForPosessingItemBase(RewardHandler):
    def to_string(self) -> str:
        return "reward_for_posessing_item"

    def xml_template(self) -> str:
        return str(
            """<RewardForPossessingItem sparse="{{ sparse | lower }}" excludeLoops="{{ exclude_loops | string | lower}}">
                    {% for item in items %}
                    <Item amount="{{ item.amount }}" reward="{{ item.reward }}" type="{{ item.type }}" />
                    {% endfor %}
                </RewardForPossessingItem>
                """
        )

    def __init__(self, sparse: bool, exclude_loops: bool, item_rewards: List[Dict[str, Union[str, int]]]):
        """
        Creates a reward which gives rewards based on items in the 
        inventory that are provided.

        See Malmo for documentation.
        """
        super().__init__()
        self.sparse = sparse
        self.exclude_loops = exclude_loops
        self.items = item_rewards
        self.reward_dict = {
            a['type']: dict(reward=a['reward'], amount=a['amount']) for a in self.items
        }
        # Assert that no amount is greater than 1.
        for k, v in self.reward_dict.items():
            assert int(v['amount']) <= 1, "Currently from universal is not implemented for item amounts > 1"

        # Assert all items have the appropriate fields for the XML template.
        for item in self.items:
            assert set(item.keys()) == {"amount", "reward", "type"}

    @abc.abstractmethod
    def from_universal(self, obs):
        raise NotImplementedError()


class RewardForCollectingItems(_RewardForPosessingItemBase):
    """
    The standard malmo reward for collecting item.

    Example usage:
    
    .. code-block:: python

        RewardForCollectingItems([
            dict(type="log", amount=1, reward=1.0),
        ])
    """

    def __init__(self, item_rewards: List[Dict[str, Union[str, int]]]):
        super().__init__(sparse=False, exclude_loops=True, item_rewards=item_rewards)

    def from_universal(self, x):
        # TODO: Now get all of these to work correctly.
        total_reward = 0
        if 'diff' in x and 'changes' in x['diff']:
            for change_json in x['diff']['changes']:
                item_name = strip_item_prefix(change_json['item'])
                if item_name == 'log2':
                    item_name = 'log'
                if item_name in self.reward_dict and 'quantity_change' in change_json:
                    if change_json['quantity_change'] > 0:
                        total_reward += change_json['quantity_change'] * self.reward_dict[item_name]['reward']
        return total_reward


class RewardForCollectingItemsOnce(_RewardForPosessingItemBase):
    """
    The standard malmo reward for collecting item once.

    Example usage:
        
    .. code-block:: python

        RewardForCollectingItemsOnce([
            dict(type="log", amount=1, reward=1),
        ])
    """

    def __init__(self, item_rewards: List[Dict[str, Union[str, int]]]):
        super().__init__(sparse=True, exclude_loops=True, item_rewards=item_rewards)
        self.seen_dict = dict()

    def from_universal(self, x):
        total_reward = 0
        if 'diff' in x and 'changes' in x['diff']:
            for change_json in x['diff']['changes']:
                item_name = strip_item_prefix(change_json['item'])
                if item_name == 'log2':
                    item_name = 'log'
                if item_name in self.reward_dict and 'quantity_change' in change_json and item_name not in self.seen_dict:
                    if change_json['quantity_change'] > 0:
                        total_reward += self.reward_dict[item_name]['reward']
                        self.seen_dict[item_name] = True
        return total_reward


# <RewardForMissionEnd>
#     <Reward description="out_of_time" reward="0" />
# </RewardForMissionEnd>
class RewardForMissionEnd(RewardHandler):
    """
    Creates a reward which is awarded when a mission ends.
    
    Example usage:
    
    .. code-block:: python

        # awards a reward of 5 when mission ends
        RewardForMissionEnd(reward=5.0, description="mission termination")
    """

    def to_string(self) -> str:
        return "reward_for_mission_end"

    def xml_template(self) -> str:
        return str(
            """<RewardForMissionEnd>
                    <Reward description="{{ description }}" reward="{{ reward }}" />
                </RewardForMissionEnd>"""
        )

    def __init__(self, reward: int, description: str = "out_of_time"):
        super().__init__()
        self.reward = reward
        self.description = description

    def from_universal(self, obs):
        # TODO: IMPLEMENT THE FROM UNVIERSAL HERE. 
        # Idea: just add an "episode terminated obs in the universal"
        # during generate.
        return 0


#  <RewardForTouchingBlockType>
#     <Block reward="100.0" type="diamond_block" behaviour="onceOnly"/>
#     <Block reward="189.0" type="diamond_block" behaviour="onceOnly"/>
# </RewardForTouchingBlockType>
class RewardForTouchingBlockType(RewardHandler):
    """
    Creates a reward which is awarded when the player touches a block.
        
    Example usage:

    .. code-block:: python

        RewardForTouchingBlockType([
            {'type':'diamond_block', 'behaviour':'onceOnly', 'reward':'10'},
        ])
    """
    def to_string(self) -> str:
        return "reward_for_touching_block_type"

    def xml_template(self) -> str:
        return str(
            """<RewardForTouchingBlockType>
                    {% for block in blocks %}
                    <Block reward="{{ block.reward }}" type="{{ block.type }}" behaviour="{{ block.behaviour }}" />
                    {% endfor %}
                </RewardForTouchingBlockType>"""
        )

    def __init__(self, blocks: List[Dict[str, Union[str, int, float]]]):
        super().__init__()
        self.blocks = blocks
        self.fired = {bl['type']: False for bl in self.blocks}
        # Assert all blocks have the appropriate fields for the XML template.
        for block in self.blocks:
            assert set(block.keys()) == {"reward", "type", "behaviour"}

    def from_universal(self, obs):
        reward = 0
        if 'touched_blocks' in obs:
            for block in obs['touched_blocks']:
                for bl in self.blocks:
                    if bl['type'] in block['name'] and (
                            not self.fired[bl['type']] or bl['behaviour'] != "onlyOnce"):
                        reward += bl['reward']
                        self.fired[bl['type']] = True

        return reward

    def reset(self):
        self.fired = {bl['type']: False for bl in self.blocks}


# <RewardForDistanceTraveledToCompassTarget rewardPerBlock="1" density="PER_TICK"/>
class RewardForDistanceTraveledToCompassTarget(RewardHandler):
    """
    Creates a reward which is awarded when the player reaches a certain distance from a target.
    
    Example usage:

    .. code-block:: python

        RewardForDistanceTraveledToCompassTarget(2)
    """

    def to_string(self) -> str:
        return "reward_for_distance_traveled_to_compass_target"

    def xml_template(self) -> str:
        return str(
            """<RewardForDistanceTraveledToCompassTarget rewardPerBlock="{{ reward_per_block }}" density="{{ density }}"/>"""
        )

    def __init__(self, reward_per_block: int, density: str = 'PER_TICK'):
        self.reward_per_block = reward_per_block
        self.density = density
        self._prev_delta = None

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
