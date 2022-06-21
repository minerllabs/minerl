# Simple env test.
import json
import select
import time
import logging

import gym
import matplotlib.pyplot as plt
import minerl
import numpy as np

import coloredlogs

coloredlogs.install(logging.DEBUG)

# import minerl.env.bootstrap
# minerl.env.bootstrap._check_port_avail = lambda _,__: True

NUM_EPISODES = 6


def main():
    """
    Tests running a simple environment.
    """
    env = gym.make('MineRLTreechop-v0')

    actions = [env.action_space.sample() for _ in range(2000)]
    xposes = []
    for i in range(NUM_EPISODES):
        env.seed(i)
        obs = env.reset()
        done = False
        netr = 0
        for _ in range(100):
            random_act = env.action_space.noop()
            # random_act['camera'] = [0, 0.1]
            # random_act['back'] = 0
            # random_act['forward'] = 1
            # random_act['jump'] = 1
            obs, reward, done, info = env.step(
                random_act)
            netr += reward
            print(reward, netr)
            env.render()
            if done:
                break

    print("Demo complete.")


if __name__ == "__main__":
    main()
