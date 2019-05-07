# Simple env test.
import json
import select
import time
import logging

import gym
import matplotlib.pyplot as plt
import minerl
import numpy as np
from minerl.env.core import MineRLEnv

import coloredlogs
coloredlogs.install(logging.DEBUG)


#import minerl.env.bootstrap
#minerl.env.bootstrap._check_port_avail = lambda _,__: True

NUM_EPISODES=10

def main():
    """
    Tests running a simple environment.
    """
    env = gym.make('MineRLNavigateDenseFixedMap-v0')
    
    actions = [env.action_space.sample() for _ in range(2000)]
    xposes = []
    for _ in range(NUM_EPISODES):
        obs, info = env.reset()
        done = False
        xpos = []
        for act in actions:
            obs, reward, done, info = env.step(
                act)
            
            if info and "XPos" in info:
                xpos.append([info["XPos"], info["YPos"], info["ZPos"], info["Yaw"], reward])
        xposes.append(xpos)


    y = np.array(xposes)
    plt.plot(y[:,:,0].T, y[:,:,2].T)
    plt.plot(y[:,:,-1].T)
    plt.show()
    print("Demo complete.")

if __name__ == "__main__":
    main()
