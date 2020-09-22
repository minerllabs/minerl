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

# import minerl.env.bootstrap
# minerl.env.bootstrap._check_port_avail = lambda _,__: True

NUM_EPISODES = 5


def main():
    """
    Tests running a simple environment.
    """
    env = gym.make('MineRLNavigateDense-v0')

    actions = [env.action_space.sample() for _ in range(2000)]
    xposes = []
    for _ in range(NUM_EPISODES):
        obs = env.reset()
        done = False
        netr = 0
        t = 0
        while not done:
            t += 1
            if t > 123:
                done = True
                break
            random_act = env.action_space.noop()

            obs, reward, done, info = env.step(
                random_act)
            # print(obs["compassAngle"])
            netr += reward
            # print(netr)
            env.render()

    print("Demo complete.")


if __name__ == "__main__":
    main()
