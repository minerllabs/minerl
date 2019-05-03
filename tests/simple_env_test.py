# Simple env test.
import json
import select
import time

import gym
import numpy as np
from numpy.core.numeric import False_

import minerl
from minerl.env.bootstrap import MinecraftInstance
from minerl.env.core import MineRLEnv

NUM_EPISODES=30

"""
1. Server observations are delayed and take a tick!
4. move watcher to java side :()
6. port binding failure.
"""

def main():
    """
    Tests running a simple environment.
    """
    env = gym.make('MineRLTreechop-v0')
    
    actions = [env.action_space.sample() for _ in range(1000)]
    xposes = []
    for _ in range(NUM_EPISODES):
        obs, info = env.reset()
        done = False
        xpos = []
        for act in actions:
            obs, reward, done, info = env.step(
                act)
            
            correct_info = json.loads(info)
            xpos.append([correct_info["XPos"], correct_info["YPos"], correct_info["ZPos"], correct_info["Yaw"]])
        xposes.append(xpos)
    
        print("MISSION DONE")
    

    y = np.array(xposes)
    from IPython import embed; embed()
    print("Demo complete.")
    




if __name__ == "__main__":
    main()