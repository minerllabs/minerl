# Simple env test.
import json
import select
import time
import logging
import threading

import gym
import matplotlib.pyplot as plt
import minerl
import numpy as np

import coloredlogs

coloredlogs.install(logging.DEBUG)

NUM_EPISODES = 1
NUM_ENVS = 2


class MineRLRunner(threading.Thread):
    def __init__(self, env_name, create_synchronously=True, **kwargs):
        self.env_name = env_name
        if create_synchronously:
            self.env = gym.make(env_name)
        else:
            self.env = None
        super().__init__(**kwargs)

    def run(self):
        env = self.env
        if env is None:
            env = gym.make(self.env_name)
        for _ in range(NUM_EPISODES):
            obs = env.reset()
            done = False
            netr = 0
            while not done:
                random_act = env.action_space.noop()

                random_act['camera'] = [0, 0.1 * obs["compass"]["angle"]]
                random_act['back'] = 0
                random_act['forward'] = 1
                random_act['jump'] = 1
                random_act['attack'] = 1
                obs, reward, done, info = env.step(
                    random_act)
                netr += reward
        env.close()
        print(f'{self.getName()} finished!')


def test(create_synchronously=True):
    threads = [MineRLRunner('MineRLNavigateDense-v0', create_synchronously) for _ in range(NUM_ENVS)]
    for t in threads:
        t.start()
    while any([t.is_alive() for t in threads]):
        time.sleep(1)


if __name__ == "__main__":
    test()
