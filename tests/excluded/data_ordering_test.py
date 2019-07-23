import time

import minerl
import itertools
import gym
import sys
import tqdm
import numpy as np


def test_data(environment='MineRLObtainDiamondDense-v0'):
    d = minerl.data.make(environment, num_workers=8)

    # Helper function
    def _check_space(key, space, observation):
        if isinstance(space, minerl.spaces.Dict):
            for k, s in space.spaces.items():
                _check_space(k, s, observation[key])
        elif isinstance(space, minerl.spaces.MultiDiscrete):
            print("MultiDiscrete")
            print(space.shape)
            print(observation[key])
        elif isinstance(space, minerl.spaces.Box):
            print("Box")
            print(space.shape)
            print(observation[key])
        elif isinstance(space, minerl.spaces.Discrete):
            print("Discrete")
            print(space.shape)
            print(observation[key])
        elif isinstance(space, minerl.spaces.Enum):
            print("Enum")
            print(space.shape)
            print(observation[key])

    # Iterate through batches of data
    counter = tqdm.tqdm()
    for obs, act, rew, nObs, done in d.sarsd_iter(num_epochs=1, max_sequence_len=128):
        correct_len = len(rew)

        for key, space in d.observation_space.items():
            _check_space(key, space, obs)

        counter.update(correct_len)

    return counter.n / counter.last_print_t if counter.last_print_n > 0 else 0


if __name__ == '__main__':
    if len(sys.argv) > 1:
        rate = test_data(sys.argv[1])
    else:
        rate = test_data()

    print("Achieved rate of {} samples per second".format(rate))


obtain_observation_space = spaces.Dict({
    'pov': spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
    'inventory': spaces.Dict({
        'dirt': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'coal': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'torch': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'log': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'planks': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'stick': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'crafting_table': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'wooden_axe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'wooden_pickaxe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'stone': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'cobblestone': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'furnace': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'stone_axe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'stone_pickaxe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'iron_ore': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'iron_ingot': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'iron_axe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
        'iron_pickaxe': spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
    }),
    'equipped_items': spaces.Dict({
        'mainhand': spaces.Dict({
            'type': spaces.Enum('none', 'air', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe',
                                'iron_axe', 'iron_pickaxe', 'other'),
            'damage': spaces.Box(low=-1, high=1562, shape=(), dtype=np.int),
            'maxDamage': spaces.Box(low=-1, high=1562, shape=(), dtype=np.int),
        })
    })
})