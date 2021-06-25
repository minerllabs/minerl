import minerl
import os
import time
from copy import deepcopy
import numpy as np
from minerl.data.util import multimap
import random

MINERL_DATA_ROOT = os.getenv('MINERL_DATA_ROOT')


def stack(*args):
    return np.stack(args)


class BufferedBatchIter:
    def __init__(self,
                 data_pipeline,
                 buffer_target_size=50000):
        self.data_pipeline = data_pipeline
        self.data_buffer = []
        self.buffer_target_size = buffer_target_size
        self.traj_sizes = []
        self.avg_traj_size = 0
        self.all_trajectories = self.data_pipeline.get_trajectory_names()
        self.available_trajectories = deepcopy(self.all_trajectories)
        random.shuffle(self.available_trajectories)

    def optionally_fill_buffer(self):
        buffer_updated = False
        while (self.buffer_target_size - len(self.data_buffer)) > self.avg_traj_size:
            if len(self.available_trajectories) == 0:
                return
            traj_to_load = self.available_trajectories.pop()
            data_loader = self.data_pipeline.load_data(traj_to_load)
            traj_len = 0
            for data_tuple in data_loader:
                traj_len += 1
                self.data_buffer.append(data_tuple)

            self.traj_sizes.append(traj_len)
            self.avg_traj_size = np.mean(self.traj_sizes)
            buffer_updated = True
        if buffer_updated:

            random.shuffle(self.data_buffer)

    def get_batch(self, batch_size):
        ret_dict_list = []
        for _ in range(batch_size):
            data_tuple = self.data_buffer.pop()
            ret_dict = dict(obs=data_tuple[0],
                            act=data_tuple[1],
                            reward=data_tuple[2],
                            next_obs=data_tuple[3],
                            done=data_tuple[4])
            ret_dict_list.append(ret_dict)
        return multimap(stack, *ret_dict_list)

    def buffered_batch_iter(self, batch_size, num_epochs=None, num_batches=None):
        assert num_batches is not None or num_epochs is not None, "One of num_epochs or " \
                                                                  "num_batches must be not-None"
        assert num_batches is None or num_epochs is None, "You cannot specify both " \
                                                          "num_batches and num_epochs"

        epoch_count = 0
        batch_count = 0

        while True:
            if num_epochs is not None and epoch_count >= num_epochs:
                return
            if num_batches is not None and batch_count >= num_batches:
                return

            self.optionally_fill_buffer()
            ret_batch = self.get_batch(batch_size=batch_size)
            batch_count += 1
            if len(self.data_buffer) < batch_size:
                assert len(self.available_trajectories) == 0, "You've reached the end of your " \
                                                              "data buffer while still having " \
                                                              "trajectories available; " \
                                                              "something seems to have gone wrong"
                epoch_count += 1
                self.available_trajectories = deepcopy(self.all_trajectories)
                random.shuffle(self.available_trajectories)

            keys = ('obs', 'act', 'reward', 'next_obs', 'done')
            yield tuple([ret_batch[key] for key in keys])


if __name__ == "__main__":

    env = "MineRLBasaltMakeWaterfall-v0"
    batch_size = 32

    start_time = time.time()
    data_pipeline = minerl.data.make(env, MINERL_DATA_ROOT)
    bbi = BufferedBatchIter(data_pipeline, buffer_target_size=10000)
    num_timesteps = 0
    for data_dict in bbi.buffered_batch_iter(batch_size=batch_size, num_epochs=1):
        num_timesteps += len(data_dict['obs']['pov'])

    print(f"{num_timesteps} found for env {env} using batch_iter")
    end_time = time.time()
    print(f"Total time: {end_time - start_time} seconds")
