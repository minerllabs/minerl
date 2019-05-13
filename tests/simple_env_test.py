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

NUM_EPISODES=5

def main():
    """
    Tests running a simple environment.
    """
    env = gym.make('MineRLTreechop-v0')
    
    actions = [env.action_space.sample() for _ in range(2000)]
    xposes = []
    for _ in range(NUM_EPISODES):
        obs, info = env.reset()
        done = False
        xpos = []
        for act in actions:
            obs, reward, done, info = env.step(
                act)
            # print("Step reward {}".format(reward))

            if info and "XPos" in obs:
                xpos.append([info["XPos"], info["ZPos"]])
        xposes.append(xpos)


    y = np.array(xposes)
    plt.plot(y[:,:,0].T, y[:,:,1].T)

    plt.show()

    # plt.plot(y[:,:,-1].T)
    # plt.show()
    # from IPython import embed; embed()
    # x1, x2 = y[:,:,-1].T
    print("Demo complete.")

if __name__ == "__main__":
    main()



