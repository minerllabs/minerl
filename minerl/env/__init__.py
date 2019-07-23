# ------------------------------------------------------------------------------------------------
# Copyright (c) 2018 Microsoft Corporation
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------
import os

# import gym
# Perform the registration.
from gym.envs.registration import register
from collections import OrderedDict
from minerl.env import spaces
from minerl.env.core import MineRLEnv, missions_dir

import numpy as np

  
register(
    id='MineRLTreechop-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'xml': os.path.join(missions_dir, 'treechop.xml'),
        'observation_space': spaces.Dict({
            'pov': spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
        }),
        'action_space': spaces.Dict(spaces={
            "forward": spaces.Discrete(2), 
            "back": spaces.Discrete(2), 
            "left": spaces.Discrete(2), 
            "right": spaces.Discrete(2), 
            "jump": spaces.Discrete(2), 
            "sneak": spaces.Discrete(2), 
            "sprint": spaces.Discrete(2), 
            "attack": spaces.Discrete(2),
            "camera": spaces.Box(low=-180, high=180, shape=(2,), dtype=np.float32),
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


#######################
#      NAVIGATE       #
#######################

def make_navigate_text(top, dense):
    navigate_text = """
.. image:: ../assets/navigate{}1.mp4.gif
    :scale: 100 %
    :alt: 

.. image:: ../assets/navigate{}2.mp4.gif
    :scale: 100 %
    :alt: 

.. image:: ../assets/navigate{}3.mp4.gif
    :scale: 100 %
    :alt: 

.. image:: ../assets/navigate{}4.mp4.gif
    :scale: 100 %
    :alt: 

In this task, the agent must move to a goal location denoted by a diamond block. This represents a basic primitive used in many tasks throughout Minecraft. In addition to standard observations, the agent has access to a “compass” observation, which points near the goal location, 64 meters from the start location. The goal has a small random horizontal offset from the compass location and may be slightly below surface level. On the goal location is a unique block, so the agent must find the final goal by searching based on local visual features.

The agent is given a sparse reward (+100 upon reaching the goal, at which point the episode terminates). """
    if dense:
        navigate_text += "**This variant of the environment is dense reward-shaped where the agent is given a reward every tick for how much closer (or negative reward for farther) the agent gets to the target.**\n"
    else: 
        navigate_text += "**This variant of the environment is sparse.**\n"

    if top is "normal":
        navigate_text += "\nIn this environment, the agent spawns on a random survival map.\n"
        navigate_text = navigate_text.format(*["" for _ in range(4)])
    else:
        navigate_text += "\nIn this environment, the agent spawns in an extreme hills biome.\n"
        navigate_text = navigate_text.format(*["extreme" for _ in range(4)])
    return navigate_text


navigate_action_space = spaces.Dict({
    "forward": spaces.Discrete(2),
    "back": spaces.Discrete(2),
    "left": spaces.Discrete(2),
    "right": spaces.Discrete(2),
    "jump": spaces.Discrete(2),
    "sneak": spaces.Discrete(2),
    "sprint": spaces.Discrete(2),
    "attack": spaces.Discrete(2),
    "camera": spaces.Box(low=-180, high=180, shape=(2,), dtype=np.float32),
    "place": spaces.Enum('none', 'dirt')})

navigate_observation_space = spaces.Dict({
    'pov': spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
    'inventory': spaces.Dict(spaces={
        'dirt': spaces.Box(low=0, high=2304, shape=(), dtype=np.int)
    }),
    'compassAngle': spaces.Box(low=-180.0, high=180.0, shape=(), dtype=np.float32)
})

register(
    id='MineRLNavigate-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'xml': os.path.join(missions_dir, 'navigation.xml'),
        'observation_space': navigate_observation_space,
        'action_space': navigate_action_space,
        'docstr': make_navigate_text('normal', False)
    },
    max_episode_steps=6000,
)

register(
    id='MineRLNavigateDense-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'xml': os.path.join(missions_dir, 'navigationDense.xml'),
        'observation_space': navigate_observation_space,
        'action_space': navigate_action_space,
        'docstr': make_navigate_text('normal', True)
    },
    max_episode_steps=6000,
)


register(
    id='MineRLNavigateExtreme-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'xml': os.path.join(missions_dir, 'navigationExtreme.xml'),
        'observation_space': navigate_observation_space,
        'action_space': navigate_action_space,
        'docstr': make_navigate_text('extreme', False) 
    },
    max_episode_steps=6000,
)

register(
    id='MineRLNavigateExtremeDense-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'xml': os.path.join(missions_dir, 'navigationExtremeDense.xml'),
        'observation_space': navigate_observation_space,
        'action_space': navigate_action_space,
        'docstr': make_navigate_text('extreme', True)  
    },
    max_episode_steps=6000,
)


#######################
#     Obtain Iron     #
#######################

obtain_observation_space = spaces.Dict({
    'pov': spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
    'inventory': spaces.Dict({
        'dirt': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'coal': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'torch': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'log': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'planks': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'stick': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'crafting_table': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'wooden_axe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'wooden_pickaxe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'stone': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'cobblestone': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'furnace': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'stone_axe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'stone_pickaxe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'iron_ore': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'iron_ingot': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'iron_axe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'iron_pickaxe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
    }),
    'equipped_items': spaces.Dict({
        'mainhand': spaces.Dict({
            'type': spaces.Enum('none', 'air', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe',
                                'iron_axe', 'iron_pickaxe', 'other'),
            'damage': spaces.Box(low=-1, high=1562, shape=(), dtype=np.int),
            'maxDamage': spaces.Box(low=-1, high=1562, shape=(), dtype=np.int),
        })
    })
})

obtain_action_space = spaces.Dict({
    "forward": spaces.Discrete(2),
    "back": spaces.Discrete(2),
    "left": spaces.Discrete(2),
    "right": spaces.Discrete(2),
    "jump": spaces.Discrete(2),
    "sneak": spaces.Discrete(2),
    "sprint": spaces.Discrete(2),
    "attack": spaces.Discrete(2),
    "camera": spaces.Box(low=-180, high=180, shape=(2,), dtype=np.float32),  # Pitch, Yaw
    "place": spaces.Enum('none', 'dirt', 'stone', 'cobblestone', 'crafting_table', 'furnace', 'torch'),
    "equip": spaces.Enum('none', 'air', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe', 'iron_pickaxe'),
    "craft": spaces.Enum('none', 'torch', 'stick', 'planks', 'crafting_table'),
    "nearbyCraft": spaces.Enum('none', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe', 'iron_pickaxe', 'furnace'),
    "nearbySmelt": spaces.Enum('none', 'iron_ingot', 'coal')})


register(
    id='MineRLObtainIronPickaxe-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'xml': os.path.join(missions_dir, 'obtainIronPickaxe.xml'),
        'observation_space': obtain_observation_space,
        'action_space': obtain_action_space,
        'docstr': """
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
    },
    max_episode_steps=6000,
)


register(
    id='MineRLObtainIronPickaxeDense-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'xml': os.path.join(missions_dir, 'obtainIronPickaxeDense.xml'),
        'observation_space': obtain_observation_space,
        'action_space': obtain_action_space,
        'docstr': """
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


During an episode the agent is rewarded **every time ** it obtains an item
in the requisite item hierarchy for obtaining an iron pickaxe. The rewards for each
item are given here::
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
    },
    max_episode_steps=6000,
)


#######################
#   Obtain Diamond    #
#######################
register(
    id='MineRLObtainDiamond-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'xml': os.path.join(missions_dir, 'obtainDiamond.xml'),
        'observation_space': obtain_observation_space,
        'action_space': obtain_action_space,
        'docstr': """
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

.. caution::
    **This is the evaluation environment of the MineRL Competition!** Specifically, you are allowed
    to train your agents on any environment (including `MineRLObtainDiamondDense-v0`_) however,
    your agent will only be evaluated on this environment..

In this environment the agent is required to obtain a diamond in 18000 steps. The agent begins in a random starting location, on a random survival map, without any items, matching the normal starting conditions for human players in Minecraft.
The agent is given access to a selected view of its inventory and GUI free
crafting, smelting, and inventory management actions.


During an episode **the agent is rewarded only once per item the first time it obtains that item
in the requisite item hierarchy for obtaining an iron pickaxe.** The reward for each
item is given here::

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
    },
    max_episode_steps=18000,
)


register(
    id='MineRLObtainDiamondDense-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'xml': os.path.join(missions_dir, 'obtainDiamondDense.xml'),
        'observation_space': obtain_observation_space,
        'action_space': obtain_action_space,
        'docstr': """
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

In this environment the agent is required to obtain a diamond. The agent begins in a random starting location on a random survival map without any items, matching the normal starting conditions for human players in Minecraft.
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
    },
    max_episode_steps=18000,
)


#######################
#        DEBUG        #
#######################

register(
    id='MineRLNavigateDenseFixed-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'xml': os.path.join(missions_dir, 'navigationDenseFixedMap.xml'),
        'observation_space': navigate_observation_space,
        'action_space': navigate_action_space,
    },
    max_episode_steps=6000,
)

register(
    id='MineRLObtainTest-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'xml': os.path.join(missions_dir, 'obtainDebug.xml'),
        'observation_space': obtain_observation_space,
        'action_space':  spaces.Dict({
            "forward": spaces.Discrete(2),
            "back": spaces.Discrete(2),
            "left": spaces.Discrete(2),
            "right": spaces.Discrete(2),
            "jump": spaces.Discrete(2),
            "sneak": spaces.Discrete(2),
            "sprint": spaces.Discrete(2),
            "attack": spaces.Discrete(2),
            "camera": spaces.Box(low=-180, high=180, shape=(2,), dtype=np.float32),  # Pitch, Yaw
            "place": spaces.Enum('none', 'dirt', 'log', 'stone', 'cobblestone', 'crafting_table', 'furnace', 'torch'),
            "equip": spaces.Enum('none', 'air', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe', 'iron_pickaxe'),
            "craft": spaces.Enum('none', 'torch', 'stick', 'planks', 'crafting_table'),
            "nearbyCraft": spaces.Enum('none', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe', 'iron_pickaxe', 'furnace'),
            "nearbySmelt": spaces.Enum('none', 'iron_ingot', 'coal')})
    },
    max_episode_steps=2000,
)
