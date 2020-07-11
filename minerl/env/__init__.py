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


# TODO: Convert to an env_spec environment
from minerl.env.unified_spaces import unified_action_space, unified_observation_space

register(
    id='UnifiedMineRL-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={
        'observation_space': unified_observation_space,
        'action_space':  unified_action_space
    },
    max_episode_steps=20 * 60 * 60 * 2, # 2 hrs
)

