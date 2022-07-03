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

NUM_EPISODES = 6


def main():
    """
    Tests running a simple environment.
    """
    #env = gym.make('MineRLBasaltMakeWaterfallHighRes-v0')
    env = gym.make('MineRLBasaltFindCaveHighRes-v0')
    print(env.action_space)
    print(env.observation_space)
    for i in range(NUM_EPISODES):
        #env.seed(i)
        obs = env.reset()
        done = False
        netr = 0
        for _ in range(100000):
            random_act = env.action_space.sample()
            obs, reward, done, info = env.step(
                random_act
            )
            netr += reward
            env.render()
            if done:
                break

if __name__ == "__main__":
    main()
