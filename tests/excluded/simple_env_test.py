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

NUM_EPISODES = 1


def test_navigate():
    """
    Tests running a simple environment.
    """
    env = gym.make('MineRLNavigateDense-v0')

    actions = [env.action_space.sample() for _ in range(2000)]
    xposes = []
    env.seed(25)
    for _ in range(NUM_EPISODES):
        obs = env.reset()
        done = False
        netr = 0
        while not done:
            random_act = env.action_space.noop()

            random_act['camera'] = [0, 0.1 * obs["compassAngle"]]
            random_act['back'] = 0
            random_act['forward'] = 1
            random_act['jump'] = 1
            random_act['attack'] = 1
            obs, reward, done, info = env.step(
                random_act)
            netr += reward
            print(reward, netr)
            env.render()

    print("Demo complete.")


def test_obfuscated():
    """
    Tests running a simple environment.
    """
    env = gym.make('MineRLObtainDiamondVectorObf-v0')
    env.seed(25)
    _ = env.reset()
    done = False
    while not done:
        random_act = env.action_space.sample()
        obs, reward, done, info = env.step(
            random_act)
        env.render()

    print("Demo complete.")

if __name__ == "__main__":
    test_obfuscated()
