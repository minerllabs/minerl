import collections
import functools
import json
import logging
import multiprocessing
from multiprocessing import Process
import os
import time
from collections import OrderedDict
from queue import PriorityQueue, Empty
from typing import List, Tuple, Any
from itertools import cycle, islice
import minerl.herobraine.env_spec
from minerl.herobraine.hero import spaces

import cv2
import os
import numpy as np
import gym

logger = logging.getLogger(__name__)

from minerl.data.version import assert_version, assert_prefix
import copy
import tqdm
import queue

import minerl.data.util
from minerl.data.util import forever, minibatch_gen
import concurrent

if os.name != "nt":
    class WindowsError(OSError):
        pass


def tree_slice(tree, slc):
    if isinstance(tree, OrderedDict):
        return OrderedDict(
            [(k, tree_slice(v, slc)) for k, v in tree.items()]
        )
    else:
        return tree[slc]


class DataPipeline:
    """
    Creates a data pipeline object used to itterate through the MineRL-v0 dataset
    """

    def __init__(self,
                 data_directory: os.path,
                 environment: str,
                 num_workers: int,
                 worker_batch_size: int,
                 min_size_to_dequeue: int,
                 random_seed=42):
        """
        Sets up a tensorflow dataset to load videos from a given data directory.
        :param data_directory:
        :type data_directory:
        :param num_workers:
        :type num_workers:
        :param worker_batch_size:
        :type worker_batch_size:
        :param min_size_to_dequeue:
        :type min_size_to_dequeue:
        :param random_seed:
        """
        self.seed = random_seed
        self.data_dir = data_directory
        self.environment = environment
        self.number_of_workers = num_workers
        self.worker_batch_size = worker_batch_size
        self.size_to_dequeue = min_size_to_dequeue
        self.processing_pool = multiprocessing.Pool(self.number_of_workers)

        self._env_spec = gym.envs.registration.spec(self.environment)._kwargs['env_spec']
        self._action_space = gym.envs.registration.spec(self.environment)._kwargs['action_space']
        self._observation_space = gym.envs.registration.spec(self.environment)._kwargs['observation_space']

    @property
    def spec(self) -> minerl.herobraine.env_spec.EnvSpec:
        return self._env_spec

    @property
    def action_space(self):
        """
        Returns: action space of current MineRL environment
        """
        return self._action_space

    @property
    def observation_space(self):
        """
        Returns: action space of current MineRL environment
        """
        return self._observation_space

        # return result

    def load_data(self, stream_name: str, skip_interval=0, include_metadata=False):
        """Iterates over an individual trajectory named stream_name.
        
        Args:
            stream_name (str): The stream name desired to be iterated through.
            skip_interval (int, optional): How many sices should be skipped.. Defaults to 0.
            include_metadata (bool, optional): Whether or not meta data about the loaded trajectory should be included.. Defaults to False.

        Yields:
            A tuple of (state, player_action, reward_from_action, next_state, is_next_state_terminal).
            These are tuples are yielded in order of the episode.
        """
        if '/' in stream_name:
            file_dir = stream_name
        else:
            file_dir = os.path.join(self.data_dir, stream_name)

        if DataPipeline._is_blacklisted(stream_name):
            raise RuntimeError("This stream is corrupted (and will be removed in the next version of the data!)")

        seq = DataPipeline._load_data_pyfunc(file_dir, -1, None, self.environment, skip_interval=skip_interval,
                                             include_metadata=include_metadata)
        if include_metadata:
            observation_seq, action_seq, reward_seq, next_observation_seq, done_seq, meta = seq
        else:
            observation_seq, action_seq, reward_seq, next_observation_seq, done_seq = seq
        # make a copty  
        gym_spec = gym.envs.registration.spec(self.environment)
        target_space = copy.deepcopy(gym_spec._kwargs['observation_space'])

        x = list(target_space.spaces.items())
        target_space.spaces = collections.OrderedDict(
            sorted(x, key=lambda x:
            x[0] if x[0] is not 'pov' else 'z')
        )

        # Now we just need to slice the dict.
        for idx in tqdm.tqdm(range(len(reward_seq))):
            # Wrap in dict
            action_dict = tree_slice(action_seq, idx)
            observation_dict = tree_slice(observation_seq, idx)
            next_observation_dict = tree_slice(next_observation_seq, idx)

            yield_list = [observation_dict, action_dict, reward_seq[idx], next_observation_dict, done_seq[idx]]
            yield yield_list + [meta] if include_metadata else yield_list

    def get_trajectory_names(self):
        """Gets all the trajectory names
        
        Returns:
            A list of experiment names: [description]
        """
        return [os.path.basename(x) for x in self._get_all_valid_recordings(self.data_dir)]

    ############################
    #     PRIVATE METHODS      #
    ############################

    @staticmethod
    def read_frame(cap):
        try:
            ret, frame = cap.read()
            if ret:
                cv2.cvtColor(frame, code=cv2.COLOR_BGR2RGB, dst=frame)
                frame = np.asarray(np.clip(frame, 0, 255), dtype=np.uint8)

            return ret, frame
        except Exception as err:
            logger.error("error reading capture device:", err)
            raise err

    @staticmethod
    def _roundrobin(*iterables):
        "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
        # Recipe credited to George Sakkis
        pending = len(iterables)
        nexts = cycle(iter(it).next for it in iterables)
        while pending:
            try:
                for next in nexts:
                    yield next()
            except StopIteration:
                pending -= 1
                nexts = cycle(islice(nexts, pending))

    # Todo: Make data pipeline split files per push.
    @staticmethod
    def _load_data_pyfunc(file_dir: str, max_seq_len: int, data_queue, env_str="", skip_interval=0,
                          include_metadata=False):
        """
        Enqueueing mechanism for loading a trajectory from a file onto the data_queue
        :param file_dir: file path to data directory
        :param skip_interval: Number of time steps to skip between each sample
        :param max_seq_len: Number of time steps in each enqueued batch
        :param data_queue: multiprocessing data queue, or None to return streams directly
        :param include_metadata: whether or not to return an additional tuple containing metadata
        :return:
        """
        logger.debug("Loading from file {}".format(file_dir))

        video_path = str(os.path.join(file_dir, 'recording.mp4'))
        numpy_path = str(os.path.join(file_dir, 'rendered.npz'))
        meta_path = str(os.path.join(file_dir, 'metadata.json'))

        try:
            # Start video decompression
            cap = cv2.VideoCapture(video_path)

            # Load numpy file
            state = np.load(numpy_path, allow_pickle=True)

            # Load metadata file
            with open(meta_path) as file:
                meta = json.load(file)
                if 'stream_name' not in meta:
                    meta['stream_name'] = file_dir

            action_dict = collections.OrderedDict([(key, state[key]) for key in state if key.startswith('action$')])
            reward_vec = state['reward']
            info_dict = collections.OrderedDict([(key, state[key]) for key in state if key.startswith('observation$')])

            # Recursively sorts nested dicts
            def recursive_sort(dct):
                for key in list(dct.keys()):
                    if isinstance(dct[key], OrderedDict):
                        dct[key] = recursive_sort(dct[key])
                        dct[key] = OrderedDict(sorted(dct[key].items()))
                return dct

            def unflatten(dct, sep='$'):
                out_dict = OrderedDict({})
                for k, v in dct.items():
                    keys = k.split(sep)
                    cur_dict = out_dict
                    for key in keys[:-1]:
                        if key not in cur_dict:
                            cur_dict[key] = OrderedDict({})
                        cur_dict = cur_dict[key]
                    cur_dict[keys[-1]] = v

                # Sort dict recursively
                recursive_sort(out_dict)
                return out_dict

            # There is no action or reward for the terminal state of an episode.
            # Hence in Publish.py we shorten the action and reward vector to reflect this.
            # We know FOR SURE that the last video frame corresponds to the last state (from Universal.json).
            num_states = len(reward_vec) + 1

            max_frame_num = meta['true_video_frame_count']

            frames = []
            frame_num, stop_idx = 0, 0

            # Advance video capture past first i-frame to start of experiment
            cap = cv2.VideoCapture(video_path)
            for _ in range(max_frame_num - num_states):
                ret, _ = DataPipeline.read_frame(cap)
                frame_num += 1
                if not ret:
                    raise RuntimeError()

            # Rendered Frames
            # Loop through the video and construct frames
            # of observations to be sent via the multiprocessing queue
            # in chunks of worker_batch_size to the batch_iter loop.

            while True:
                ret = True
                start_idx = stop_idx

                # Collect up to worker_batch_size number of frames
                try:
                    # Go until max_seq_len +1 for S_t, A_t,  -> R_t, S_{t+1}, D_{t+1}
                    while ret and frame_num < max_frame_num and (len(frames) < max_seq_len + 1 or max_seq_len == -1):
                        ret, frame = DataPipeline.read_frame(cap)
                        frames.append(frame)
                        frame_num += 1

                except Exception as err:
                    logger.error("error reading capture device:", err)
                    raise err

                if len(frames) <= 1:
                    break

                if frame_num == max_frame_num:
                    frames[-1] = frames[-2]

                # Next sarsd pair index
                stop_idx = start_idx + len(frames) - 1
                # print('Num frames in batch:', stop_idx - start_idx)

                # Load non-image data from npz
                current_observation_data = OrderedDict()
                action_data = OrderedDict()
                next_observation_data = OrderedDict()

                try:
                    for key in list(info_dict.keys()) + ['observation$pov']:
                        if 'pov' in key:
                            current_observation_data[key] = np.asanyarray(frames[:-1])
                            next_observation_data[key] = np.asanyarray(frames[1:])
                        else:
                            current_observation_data[key] = np.asanyarray(info_dict[key][start_idx:stop_idx])
                            next_observation_data[key] = np.asanyarray(info_dict[key][start_idx + 1:stop_idx + 1])

                    # We are getting (S_t, A_t -> R_t),   S_{t+1}, D_{t+1} so there are less actions and rewards
                    for key in action_dict:
                        action_data[key] = np.asanyarray(action_dict[key][start_idx: stop_idx])

                    reward_data = np.asanyarray(reward_vec[start_idx:stop_idx], dtype=np.float32)

                    done_data = [False for _ in range(len(reward_data))]
                    if frame_num == max_frame_num:
                        done_data[-1] = True
                except Exception as err:
                    logger.error("error drawing batch from npz file:", err)
                    raise err

                # unflatten these dictioanries.
                current_observation_data = unflatten(current_observation_data)['observation']
                action_data = unflatten(action_data)['action']
                next_observation_data = unflatten(next_observation_data)['observation']

                batches = [current_observation_data, action_data, reward_data, next_observation_data,
                           np.array(done_data, dtype=np.bool)]

                if include_metadata:
                    batches += [meta]

                if data_queue is None:
                    return batches
                else:
                    data_queue.put(batches)
                    logger.debug("Enqueued from file {}".format(file_dir))

                if not ret:
                    break
                else:
                    frames = [frames[-1]]

            logger.error("Finished")
            return None
        except WindowsError as e:
            logger.debug("Caught windows error {} - this is expected when closing the data pool".format(e))
            return None
        except FileNotFoundError as e:
            print("File not found!")
            raise e
        except Exception as e:
            logger.error("Exception caught on file \"{}\" by a worker of the data pipeline.".format(file_dir))
            logger.error(repr(e))
            return None

    def batch_iter(self,
                   batch_size: int,
                   seq_len: int,
                   num_epochs: int = -1,
                   preload_buffer_size: int = 2,
                   seed: int = None,
                   include_metadata: bool = False):
        """Returns batches of sequences length SEQ_LEN of the data of size BATCH_SIZE.
        The iterator produces batches sequentially. If an element of a batch reaches the
        end of its 


        Args:
            batch_size (int): The batch size.
            seq_len (int): The size of sequences to produce.
            num_epochs (int, optional): The number of epochs to iterate over the data. Defaults to -1.
            preload_buffer_size (int, optional): Increase to IMPROVE PERFORMANCE. The data iterator uses a queue to prevent blocking, the queue size is the number of trajectories to load into the buffer. Adjust based on memory constraints. Defaults to 32.
            seed (int, optional): [int]. NOT IMPLEMENTED Defaults to None.
            include_metadata (bool, optional): Include metadata on the source trajectory. Defaults to False.

        Returns:
            Generator: A generator that yields (sarsd) batches
        """
        # Todo: Not implemented/
        input_queue = multiprocessing.Queue()
        trajectory_queue = multiprocessing.Queue(maxsize=preload_buffer_size)

        workers = []
        args = (input_queue, trajectory_queue)
        for _ in range(self.number_of_workers):
            workers.append(Process(target=loader_func, args=args))
            workers[-1].start()

        for epoch in (range(num_epochs) if num_epochs > 0 else forever()):

            def traj_iter():
                for _ in jobs:
                    data_tuple = trajectory_queue.get()
                    if data_tuple is None:
                        continue
                    s, a, r, sp1, d = data_tuple
                    yield dict(
                        obs=s,
                        act=a,
                        reward=r,
                        next_obs=sp1,
                        done=d
                    )

            jobs = [(f, -1, None)
                    for f in self._get_all_valid_recordings(self.data_dir)]
            np.random.shuffle(jobs)
            for job in jobs:
                input_queue.put(job)

            for seg_batch in minibatch_gen(traj_iter(), batch_size=batch_size, nsteps=seq_len):
                yield seg_batch['obs'], seg_batch['act'], seg_batch['reward'], seg_batch['next_obs'], seg_batch['done']

        for _ in range(self.number_of_workers):
            input_queue.put(("SHUTDOWN",))

        for w in workers:
            w.join()

    @staticmethod
    def _is_blacklisted(path):
        for p in [
            'tempting_capers_shapeshifter-14'
        ]:
            if p in path:
                return True

        return False

    @staticmethod
    def _get_all_valid_recordings(path):
        directoryList = []

        # return nothing if path is a file
        if os.path.isfile(path):
            return []

        # Skip this file.
        if DataPipeline._is_blacklisted(path):
            return []

        # add dir to directory list if it contains .txt files
        if len([f for f in os.listdir(path) if f.endswith('.mp4')]) > 0:
            if len([f for f in os.listdir(path) if f.endswith('.npz')]) > 0:
                assert_prefix(path)
                directoryList.append(path)

        for d in os.listdir(path):
            new_path = os.path.join(path, d)
            if os.path.isdir(new_path):
                directoryList += DataPipeline._get_all_valid_recordings(new_path)

        directoryList = np.array(directoryList)
        np.random.shuffle(directoryList)
        return directoryList.tolist()

    ###
    # DEPRECATED API
    ###
    def seq_iter(self, num_epochs=-1, max_sequence_len=32, queue_size=None, seed=None, include_metadata=False):
        """DEPRECATED METHOD FOR SAMPLING DATA FROM THE MINERL DATASET.

        This function is now :code:`DataPipeline.batch_iter()`
        """
        raise DeprecationWarning(
            "The `DataPipeline.seq_iter` method is deprecated! Please use DataPipeline.batch_iter()."
            "\nNOTE: The new method `DataPipeline.batch_iter` has a different return signature! "
            "\n\t  Please see how to use it @ http://www.minerl.io/docs/tutorials/data_sampling.html")

    def sarsd_iter(self, num_epochs=-1, max_sequence_len=32, queue_size=None, seed=None, include_metadata=False):
        """
        Returns a generator for iterating through (state, action, reward, next_state, is_terminal)
        tuples in the dataset.
        Loads num_workers files at once as defined in minerl.data.make() and return up to
        max_sequence_len consecutive samples wrapped in a dict observation space
        
        Args:
            num_epochs (int, optional): number of epochs to iterate over or -1
                to loop forever. Defaults to -1
            max_sequence_len (int, optional): maximum number of consecutive samples - may be less. Defaults to 32
            seed (int, optional): seed for random directory walk - note, specifying seed as well as a finite num_epochs
                will cause the ordering of examples to be the same after every call to seq_iter
            queue_size (int, optional): maximum number of elements to buffer at a time, each worker may hold an
                additional item while waiting to enqueue. Defaults to 16*self.number_of_workers or 2*
                self.number_of_workers if max_sequence_len == -1
            include_metadata (bool, optional): adds an additional member to the tuple containing metadata about the
                stream the data was loaded from. Defaults to False

        Yields:
            A tuple of (state, player_action, reward_from_action, next_state, is_next_state_terminal, (metadata)).
            Each element is in the format of the environment action/state/reward space and contains as many
            samples are requested.
        """
        raise DeprecationWarning(
            "The `DataPipeline.sarsd_iter` method is deprecated! Please use DataPipeline.batch_iter().")


def loader_func(input_queue, output_queue):
    while True:
        arg = input_queue.get()
        if arg[0] == "SHUTDOWN":
            break
        output = DataPipeline._load_data_pyfunc(*arg)
        output_queue.put(output)
