import time

import minerl
import itertools
import gym
import sys
import tqdm
import numpy as np


def time_data(environment='MineRLObtainDiamond-v0'):
    d = minerl.data.make(environment, num_workers=8)

    # Iterate through batches of data
    counter = tqdm.tqdm()
    for obs, act, rew, nObs, done in itertools.islice(d.sarsd_iter(num_epochs=1, max_sequence_len=128), 1000):
        counter.update(len(rew))

    return counter.n / counter.last_print_t if counter.last_print_n > 0 else 0


if __name__ == '__main__':
    if len(sys.argv) > 1:
        rate = time_data(sys.argv[1])
    else:
        rate = time_data()

    print("Achieved rate of {} samples per second".format(rate))


def test_data():
    assert (time_data() > 0)
