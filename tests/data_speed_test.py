import time

import minerl
import itertools
import gym
import sys
import tqdm
import numpy as np

NUM_EPISODES = 4
ENVIRONMENTS = [
    'MineRLTreechop-v0',
    'MineRLNavigate-v0',
    'MineRLNavigateDense-v0',
    'MineRLNavigateExtreme-v0',
    'MineRLNavigateExtremeDense-v0',
    'MineRLObtainIronPickaxe-v0',
    'MineRLObtainDiamond-v0',
]


def step_data(environment='MineRLObtainDiamondDense-v0'):
    d = minerl.data.make(environment, num_workers=8)

    # Iterate through batches of data
    counter = tqdm.tqdm()
    # for obs, rew, done, act in itertools.islice(d.seq_iter(max_sequence_len=32), 6000):
    for obs, rew, done, act in d.seq_iter(num_epochs=1, max_sequence_len=128):
        counter.update(len(rew))

if __name__ == '__main__':
    if len(sys.argv) > 0:
        if sys.argv[1] not in ENVIRONMENTS:
            print('Warning {} not found in existing environment list - is this a new environment?')
        step_data(sys.argv[1])
    else:
        step_data()
