import minerl
import os
import pytest
import tqdm
from minerl.data import BufferedBatchIter


has_minerl_data_root = os.environ.get("MINERL_DATA_ROOT") is not None

# We haven't figured out the right way to download the minimal MineRL dataset into
# the CircleCI/Docker yet. Until then, allow these tests to pass when MINERL_DATA_ROOT
# is not set (indicating that we don't have data available to test).
#
# TODO(shwang): Get these tests passing on CircleCI.
skipif_no_data = pytest.mark.skipif(
    not has_minerl_data_root,
    reason="MINERL_DATA_ROOT not set",
)


@skipif_no_data
def test_batch_iter():
    dat = minerl.data.make('MineRLTreechopVectorObf-v0')

    i = 0
    for (current_state, action,
         reward, next_state, done) in tqdm.tqdm(dat.batch_iter(1, 32, 1, preload_buffer_size=2)):
        i += 1
        if i > 100:
            # assert False
            break


@skipif_no_data
def test_buffered_batch_iter():
    dat = minerl.data.make('MineRLTreechopVectorObf-v0')
    bbi = BufferedBatchIter(dat)
    i = 0
    for (current_state, action,
         reward, next_state, done) in tqdm.tqdm(bbi.buffered_batch_iter(batch_size=10,
                                                                        num_batches=200)):

        print(current_state['pov'][0])
        print(reward[-1])
        print(done[-1])
        i += 1
        if i > 100:
            # assert False
            break
        pass
