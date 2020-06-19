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
from minerl.env.core import MineRLEnv, missions_dir
from minerl.env.recording import MineRLRecorder, MINERL_RECORDING_PATH

# TODO: Properly integrate recording.

import numpy as np

# register(
#     id='MineRLTreechopDebug-v0',
#     entry_point=entry_point,
#     kwargs={
#         'xml': os.path.join(missions_dir, 'treechopDebug.xml'),
#         'observation_space': spaces.Dict({
#             'pov': spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
#         }),
#         'action_space': spaces.Dict(spaces={
#             "forward": spaces.Discrete(2), 
#             "back": spaces.Discrete(2), 
#             "left": spaces.Discrete(2), 
#             "right": spaces.Discrete(2), 
#             "jump": spaces.Discrete(2), 
#             "sneak": spaces.Discrete(2), 
#             "sprint": spaces.Discrete(2), 
#             "attack": spaces.Discrete(2),
#             "camera": spaces.Box(low=-180, high=180, shape=(2,), dtype=np.float32),
#         }),
#         'docstr': """
#         In treechop debug, the agent must collect 2 `minercaft:log`. This tests the handlers for rewards and completion.

#         The agent begins in a forest biome (near many trees) with an iron axe for cutting trees. The agent is given +1 reward for obtaining each unit of wood, and the episode terminates once the agent obtains 64 units.\n"""
#             },
#             max_episode_steps=1000,
#             reward_threshold=2.0,
# )

# register(
#     id='MineRLObtainTest-v0',
#     entry_point='minerl.env:MineRLEnv',
#     kwargs={
#         'xml': os.path.join(missions_dir, 'obtainDebug.xml'),
#         'observation_space': obtain_observation_space,
#         'action_space':  spaces.Dict({
#             "forward": spaces.Discrete(2),
#             "back": spaces.Discrete(2),
#             "left": spaces.Discrete(2),
#             "right": spaces.Discrete(2),
#             "jump": spaces.Discrete(2),
#             "sneak": spaces.Discrete(2),
#             "sprint": spaces.Discrete(2),
#             "attack": spaces.Discrete(2),
#             "camera": spaces.Box(low=-180, high=180, shape=(2,), dtype=np.float32),  # Pitch, Yaw
#             "place": spaces.Enum('none', 'dirt', 'log', 'log2', 'stone', 'cobblestone', 'crafting_table', 'furnace', 'torch', 'diamond_ore'),
#             "equip": spaces.Enum('none', 'red_flower', 'air', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe', 'iron_pickaxe'),
#             "craft": spaces.Enum('none', 'torch', 'stick', 'planks', 'crafting_table'),
#             "nearbyCraft": spaces.Enum('none', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe', 'iron_pickaxe', 'furnace'),
#             "nearbySmelt": spaces.Enum('none', 'iron_ingot', 'coal')})
#     },
#     max_episode_steps=2000,
# )

# register(
#     id='MineRLObtainTestDense-v0',
#     entry_point='minerl.env:MineRLEnv',
#     kwargs={
#         'xml': os.path.join(missions_dir, 'obtainDebugDense.xml'),
#         'observation_space': obtain_observation_space,
#         'action_space':  spaces.Dict({
#             "forward": spaces.Discrete(2),
#             "back": spaces.Discrete(2),
#             "left": spaces.Discrete(2),
#             "right": spaces.Discrete(2),
#             "jump": spaces.Discrete(2),
#             "sneak": spaces.Discrete(2),
#             "sprint": spaces.Discrete(2),
#             "attack": spaces.Discrete(2),
#             "camera": spaces.Box(low=-180, high=180, shape=(2,), dtype=np.float32),  # Pitch, Yaw
#             "place": spaces.Enum('none', 'dirt', 'log', 'log2', 'stone', 'cobblestone', 'crafting_table', 'furnace', 'torch', 'diamond_ore'),
#             "equip": spaces.Enum('none', 'red_flower', 'air', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe', 'iron_pickaxe'),
#             "craft": spaces.Enum('none', 'torch', 'stick', 'planks', 'crafting_table'),
#             "nearbyCraft": spaces.Enum('none', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe', 'iron_pickaxe', 'furnace'),
#             "nearbySmelt": spaces.Enum('none', 'iron_ingot', 'coal')})
#     },
#     max_episode_steps=2000,
# )
