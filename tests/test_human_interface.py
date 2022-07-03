import logging
import minerl
import gym
from minerl.human_play_interface.human_play_interface import HumanPlayInterface

import coloredlogs
coloredlogs.install(logging.DEBUG)

ENV_NAMES = [
    "MineRLBasaltFindCave-v0",
    "MineRLBasaltMakeWaterfall-v0",
    "MineRLBasaltCreateVillageAnimalPen-v0",
    "MineRLBasaltBuildVillageHouse-v0", 
    'MineRLTreechop-v0',  # Doesn't work because it isn't a HumanEmbodied environment
]

def test_human_interface():
    env = gym.make(ENV_NAMES[3])
    env = HumanPlayInterface(env)
    env.reset()
    done = False
    while not done:
        _, _, done, _ = env.step()
    print("Episode done")
    env.close()

if __name__ == '__main__':
    test_human_interface()
