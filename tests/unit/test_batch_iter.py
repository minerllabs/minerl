import minerl
import os
import coloredlogs
import logging
import numpy as np
import tqdm


def test_batch_iter():
    dat = minerl.data.make('MineRLTreechopVectorObf-v0')

    act_vectors = []
    for _ in tqdm.tqdm(dat.batch_iter(16, 32, 1, preload_buffer_size=20)):
        pass


if __name__ == '__main__':
    # coloredlogs.install(logging.DEBUG)
    os.environ['MINERL_DATA_ROOT'] = os.path.expanduser('~/adsd')
    test_batch_iter()
