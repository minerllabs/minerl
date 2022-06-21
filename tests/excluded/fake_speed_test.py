# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import json
import select
import time
import logging

import gym
# import matplotlib.pyplot as plt
import minerl
import numpy as np
from minerl.env.core import MineRLEnv

import coloredlogs

coloredlogs.install(logging.DEBUG)

NUM_EPISODES = 10


def main():
    """
    Test fake speed test
    """
    env = gym.make('FakeMineRLNavigateDense-v0')

    random_act = env.action_space.noop()
    random_act['camera'] = [0, 0.1]
    random_act['back'] = 0
    random_act['forward'] = 1
    random_act['jump'] = 1
    random_act['attack'] = 1
    nsteps = 0
    avg_time = 0
    reward_list = []
    for _ in range(NUM_EPISODES):
        env.seed(22)
        obs = env.reset()
        done = False
        netr = 0
        rewards = []
        while (not done and not nsteps % 50 == 0) or nsteps == 0:
            # if(len(rewards) > 50):

            # print(random_act)
            t0 = time.time()
            obs, reward, done, info = env.step(
                random_act)
            avg_time += (1 / (time.time() - t0))
            nsteps += 1

    print(" AVERAGE FPS WITHOUT MINECRAFT: " + str(avg_time / nsteps))


if __name__ == "__main__":
    main()
