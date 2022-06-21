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

def gen_obtain_debug_actions(env):
    actions = []

    def act(**kwargs):
        action = env.action_space.no_op()
        for key, value in kwargs.items():
            action[key] = value
        actions.append(action)

    [act(forward=1, jump=1) for _ in range(10)]

    act(camera=np.array([-45.0, 0.0], dtype=np.float32))
    [act(attack=1) for _ in range(40)]

    act(camera=np.array([45.0, 0.0], dtype=np.float32))

    [act(forward=1, jump=1) for _ in range(3)]

    [act(forward=1) for _ in range(5)]

    act(camera=np.array([-90, 0.0], dtype=np.float32))

    [act(attack=1) for _ in range(40)]

    return actions


def main():
    """
    Tests running a simple environment.
    """
    env = gym.make('MineRLTreechop-v0')

    env.seed(17)
    obs = env.reset()
    done = False
    netr = 0
    for action in gen_obtain_debug_actions(env):
        obs, reward, done, info = env.step(action)
        time.sleep(0.1)
        env.render()
        if reward != 0:
            print(reward)
        if done:
            print('done!')
            break

    print("Demo complete.")


if __name__ == "__main__":
    main()
