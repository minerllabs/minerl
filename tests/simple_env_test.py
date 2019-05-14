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
    env = gym.make('MineRLNavigate-v0')
    
    actions = [env.action_space.sample() for _ in range(2000)]
    xposes = []
    for _ in range(NUM_EPISODES):
        obs, info = env.reset()
        done = False
        xpos = []
        while not done:
            random_act = env.action_space.sample()
            
            random_act['camera'] = [0, 0.05*obs["compassAngle"]]
            random_act['back'] = 0
            random_act['jump'] = 1
            random_act['attack'] = 1
            # print(random_act)
            obs, reward, done, info = env.step(
                random_act)
            print(obs["compassAngle"])
            # print("Step reward {}".format(reward))

            if "XPos" in obs and "ZPos" in obs:
                xpos.append([obs["XPos"], obs["ZPos"]])
        xposes.append(xpos)


    y = np.array(xposes)
    plt.plot(y[:,:,0].T, y[:,:,1].T)

    plt.show()

    print("Demo complete.")

if __name__ == "__main__":
    main()



