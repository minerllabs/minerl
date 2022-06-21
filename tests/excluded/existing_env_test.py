import os
import numpy as np
import gym
import logging

import minerl

from minerl.env import missions_dir
from minerl.env.core import MineRLEnv

import coloredlogs

coloredlogs.install(logging.DEBUG)


def main(port):
    args = {
        'xml': os.path.join(missions_dir, 'treechop.xml'),
        'observation_space': gym.spaces.Dict({
            'pov': gym.spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
            # 'XPos': gym.spaces.Box(low=-100000, high=100000, shape=(1,), dtype=np.int32),
            # 'ZPos': gym.spaces.Box(low=-100000, high=100000, shape=(1,), dtype=np.int32)
        }),
        'action_space': gym.spaces.Dict({
            "forward": gym.spaces.Discrete(2),
            "back": gym.spaces.Discrete(2),
            "left": gym.spaces.Discrete(2),
            "right": gym.spaces.Discrete(2),
            "jump": gym.spaces.Discrete(2),
            "sneak": gym.spaces.Discrete(2),
            "sprint": gym.spaces.Discrete(2),
            "attack": gym.spaces.Discrete(2),
            "camera": gym.spaces.Box(low=-180, high=180, shape=(2,), dtype=np.float32),
        }),
        'port': port
    }

    env = MineRLEnv(**args)

    print("Testing reset!")
    env.reset()

    done = False
    t = 0
    print("Running episode.")
    while not done:
        t += 1
        if t % 1000 == 0:
            print("Stepped {} times".format(t))
        s, r, done, _i = env.step(env.action_space.sample())
    print("Episode complete!")


if __name__ == "__main__":
    main(9000)
