import minerl
import os
import coloredlogs
import logging
import numpy as np
import tqdm
from minerl.data import BufferedBatchIter


def test_batch_iter():
    dat = minerl.data.make('MineRLTreechopVectorObf-v0')

    i = 0
    for current_state, action, reward, next_state, done in tqdm.tqdm(dat.batch_iter(1, 32, 1, preload_buffer_size=2)):
        i += 1
        if i > 100:
            # assert False
            break
        pass


def test_buffered_batch_iter():
    dat = minerl.data.make('MineRLTreechopVectorObf-v0')
    bbi = BufferedBatchIter(dat)
    i = 0
    for current_state, action, reward, next_state, done in tqdm.tqdm(bbi.buffered_batch_iter(batch_size=10, num_batches=200)):

        print(current_state['pov'][0])
        print(reward[-1])
        print(done[-1])
        i += 1
        if i > 100:
            # assert False
            break
        pass