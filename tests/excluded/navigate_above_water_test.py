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
coloredlogs.install(logging.INFO)



NUM_EPISODES=1

def main():
    """
    Tests running a simple environment.
    """
    env = gym.make('MineRLNavigateDense-v0')
    env.seed(420)
    for _ in range(NUM_EPISODES):
        obs = env.reset()
        done = False
        netr = 0
        while not done:
            random_act = env.action_space.noop()
            
            random_act['camera'] = [0, 0.1*obs["compassAngle"]]
            random_act['back'] = 0
            random_act['forward'] = 1
            random_act['jump'] = 1
            random_act['attack'] = 1
            obs, reward, done, info = env.step(
                random_act)
            netr += reward
            env.render()



    print("Demo complete.")

if __name__ == "__main__":
    main()
