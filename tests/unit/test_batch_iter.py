import minerl
import os
import coloredlogs
import logging
import numpy as np
import tqdm


def test_batch_iter():
    dat = minerl.data.make('MineRLTreechopVectorObf-v0')

    act_vectors = []
    i = 0
    for _ in tqdm.tqdm(dat.batch_iter(1, 32, 1, preload_buffer_size=2)):
        i += 1
        print(i)
        if i > 100:
            # assert False
            break
        pass
