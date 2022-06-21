# Simple env test.
import json
import select
import time
import logging

import gym
import os
import matplotlib.pyplot as plt
import minerl
import numpy as np
from minerl.env.core import MineRLEnv

import coloredlogs

coloredlogs.install(logging.DEBUG)

# import minerl.env.bootstrap
# minerl.env.bootstrap._check_port_avail = lambda _,__: True

NUM_EPISODES = 1


def main():
    """
    Tests running a simple environment.
    """
    os.environ["AICROWD_IS_GRADING"] = "1"
    env = gym.make('MineRLNavigateDense-v0')

    for _ in range(NUM_EPISODES):
        obs = env.reset()
        done = False
        netr = 0
        while not done:
            random_act = env.action_space.noop()

            # TODO: ADD ASSERTION FOR IF RENDER CALL HAPPENS!
            env.render()
            env.step(random_act)

    print("Demo complete.")


if __name__ == "__main__":
    main()
