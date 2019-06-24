import json
import logging
import multiprocessing
import os
import time
from collections import OrderedDict
from queue import PriorityQueue, Empty
from typing import List, Tuple, Any
from itertools import cycle, islice
from minerl.env import spaces

import cv2
import os
import numpy as np
import gym

logger = logging.getLogger(__name__)

if os.name != "nt":
    class WindowsError(OSError):
        pass


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

    # Correct way
    # @staticmethod
    # def map_to_dict(handler_list: list, target_space: gym.spaces.space):
    #
    #     def _map_to_dict(i: int, src: list, key: str, gym_space: gym.spaces.space, dst: dict):
    #         if isinstance(gym_space, spaces.Dict):
    #             inner = dict()
    #             for idx, (k, s) in enumerate(gym_space.spaces.items()):
    #                 _map_to_dict(idx, src[i], k, s, inner)
    #             dst[key] = inner
    #         else:
    #             dst[key] = src[i]
    #     result = dict()
    #     for index, (key, space) in enumerate(target_space.spaces.items()):
    #         _map_to_dict(index, handler_list, key, space, result)
    #     return result

    @staticmethod
    def map_to_dict(handler_list: list, target_space: gym.spaces.space):

        def _map_to_dict(i: int, src: list, key: str, gym_space: gym.spaces.space, dst: dict):
            if isinstance(gym_space, spaces.Dict):
                dont_count = False
                inner_dict = dict()
                for idx, (k, s) in enumerate(gym_space.spaces.items()):
                    if key in ['equipped_items', 'mainhand']:
                        dont_count = True
                        i = _map_to_dict(i, src, k, s, inner_dict)
                    else:
                        _map_to_dict(idx, src[i].T, k, s, inner_dict)
                dst[key] = inner_dict
                if dont_count:
                    return i
                else:
                    return i + 1
            else:
                dst[key] = src[i]
                return i + 1
        result = dict()
        index = 0
        for key, space in target_space.spaces.items():
            index = _map_to_dict(index, handler_list, key, space, result)
        return result

    def seq_iter(self, num_epochs=-1, max_sequence_len=32, seed=None):
        """
        Returns a generator for iterating through sequences of the dataset.
        Loads num_workers files at once as defined in minerl.data.make() and return up to
        max_sequence_len consecutive samples wrapped in a dict observation space
        
        Args:
            num_epochs (int, optional): number of epochs to ittereate over or -1
             to loop forever. Defaults to -1.
            max_sequence_len (int, optional): maximum number of consecutive samples - may be less. Defaults to 32.
            seed (int, optional): seed for random directory walk - note, specifying seed as well as a finite num_epochs
             will cause the ordering of examples to be the same after every call to seq_iter

        Generates:
            observation_dict, reward_list, done_list, action_dict
        """

        logger.info("Starting seq iterator on {}".format(self.data_dir))
        if seed is not None:
            np.random.seed(seed)
        data_list = self._get_all_valid_recordings(self.data_dir)

        m = multiprocessing.Manager()
        if max_sequence_len == -1:
            max_size = 2*self.number_of_workers
        else:
            max_size = 16*self.number_of_workers
        data_queue = m.Queue(maxsize=max_size)

        # Setup arguments for the workers.
        files = [(file_dir, max_sequence_len, data_queue) for file_dir in data_list]

        epoch = 0

        while epoch < num_epochs or num_epochs == -1:

            # Debug
            # for arg1, arg2, arg3 in files:
            #     DataPipeline._load_data_pyfunc(arg1, arg2, arg3)
            #     break

            map_promise = self.processing_pool.starmap_async(DataPipeline._load_data_pyfunc, files)

            # random_queue = PriorityQueue(maxsize=pool_size)

            # We map the files -> load_data -> batch_pool -> random shuffle -> yield.
            while True:
                try:
                    sequence = data_queue.get_nowait()
                    action_batch, observation_batch, reward_batch, done_batch = sequence

                    # Wrap in dict
                    gym_spec = gym.envs.registration.spec(self.environment)

                    action_dict = self.map_to_dict(action_batch, gym_spec._kwargs['action_space'])
                    observation_dict = self.map_to_dict(observation_batch, gym_spec._kwargs['observation_space'])

                    yield observation_dict, reward_batch[0], done_batch[0], action_dict
                except Empty:
                    if map_promise.ready():
                        epoch += 1
                        break
                    else:
                        time.sleep(0.1)

        logger.info("Epoch complete.")

    @staticmethod
    def load_data(file_dir: str, environment: str, skip_interval=0,):
        """
        Loading mechanism for loading a trajectory from a file as a generator
        :param file_dir: file path to data directory
        :param environment: the environment name e.g. MineRLObtainDiamond-v0
        :param skip_interval: NOT IMPLEMENTED how many frames to skip between observations
        :return: iterator over files
        """

        DataPipeline._load_data_pyfunc(file_dir, -1, None, skip_interval=skip_interval, environment=environment)

    ############################
    #     PRIVATE METHODS      #
    ############################

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
    def _load_data_pyfunc(file_dir: str, max_seq_len: int, data_queue, skip_interval=0, environment=None):
        """
        Enqueueing mechanism for loading a trajectory from a file onto the data_queue
        :param file_dir: file path to data directory
        :param skip_interval: Number of time steps to skip between each sample
        :param max_seq_len: Number of time steps in each enqueued batch
        :param data_queue: multiprocessing data queue, or None to return streams directly
        :param environment: environment used to wrap returned data as dict, or None to return raw data
        :return:
        """

        video_path = str(os.path.join(file_dir, 'recording.mp4'))
        numpy_path = str(os.path.join(file_dir, 'rendered.npz'))

        try:
            # Start video decompression
            cap = cv2.VideoCapture(video_path)

            # Load numpy file
            state = np.load(numpy_path, allow_pickle=True)

            action_dict = {key: state[key] for key in state if key.startswith('action_')}
            reward_vec = state['reward']
            info_dict = {key: state[key] for key in state if key.startswith('observation_')}

            num_states = len(reward_vec)

            # Rendered Frames
            frame_num, stop_idx = 0, 0
            max_frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            observables = list(info_dict.keys()).copy()
            observables.append('pov')
            actionables = list(action_dict.keys())

            # Advance video capture past first i-frame to start of experiment
            for _ in range(max_frame_num - num_states):
                ret, _ = cap.read()
                frame_num += 1
                if not ret:
                    return None

            # Loop through the video and construct frames
            # of observations to be sent via the multiprocessing queue
            # in chunks of worker_batch_size to the batch_iter loop.
            while True:
                ret = True
                frames = []
                start_idx = stop_idx

                # Collect up to worker_batch_size number of frames
                try:
                    while ret and frame_num < max_frame_num and (len(frames) < max_seq_len or max_seq_len == -1):
                        ret, frame = cap.read()
                        if ret:
                            cv2.cvtColor(frame, code=cv2.COLOR_BGR2RGB, dst=frame)
                            frames.append(np.asarray(np.clip(frame, 0, 255), dtype=np.uint8))
                            frame_num += 1
                except Exception as err:
                    print("error reading capture device:", err)
                    raise err

                if len(frames) == 0:
                    break

                stop_idx = start_idx + len(frames)
                # print('Num frames in batch:', stop_idx - start_idx)

                # Load non-image data from npz
                observation_data = [None for _ in observables]
                action_data = [None for _ in actionables]

                try:
                    for i, key in enumerate(observables):
                        if key == 'pov':
                            observation_data[i] = np.asanyarray(frames)
                        else:
                            observation_data[i] = np.asanyarray(state[key][start_idx:stop_idx])

                    for i, key in enumerate(actionables):
                        action_data[i] = np.asanyarray(state[key][start_idx:stop_idx])

                    reward_data = np.asanyarray(reward_vec[start_idx:stop_idx], dtype=np.float32)

                    done_data = [False for _ in range(stop_idx - start_idx)]
                    if frame_num == max_frame_num:
                        done_data[-1] = True
                except Exception as err:
                    print("error drawing batch from npz file:", err)
                    raise err

                # batches = tuple((action_data, observation_data, reward_data))
                batches = [action_data, observation_data, [reward_data], [np.array(done_data, dtype=np.bool)]]

                if data_queue is None:
                    action_batch, observation_batch, reward_batch, done_batch = batches

                    # Wrap in dict
                    gym_spec = gym.envs.registration.spec(environment)
                    action_dict = DataPipeline.map_to_dict(action_batch, gym_spec._kwargs['action_space'])
                    observation_dict = DataPipeline.map_to_dict(observation_batch,gym_spec._kwargs['observation_space'])

                    return observation_dict, reward_batch[0], done_batch[0], action_dict
                else:
                    data_queue.put(batches)

                if not ret:
                    break

            # logger.error("Finished")
            return None
        except WindowsError as e:
            logger.info("Caught windows error {} - this is expected when closing the data pool".format(e))
            return None
        except Exception as e:
            logger.error("Exception \'{}\' caught on file \"{}\" by a worker of the data pipeline.".format(e, file_dir))
            return None

    @staticmethod
    def _get_all_valid_recordings(path):
        directoryList = []

        # return nothing if path is a file
        if os.path.isfile(path):
            return []

        # add dir to directorylist if it contains .txt files
        if len([f for f in os.listdir(path) if f.endswith('.mp4')]) > 0:
            if len([f for f in os.listdir(path) if f.endswith('.npz')]) > 0:
                directoryList.append(path)

        for d in os.listdir(path):
            new_path = os.path.join(path, d)
            if os.path.isdir(new_path):
                directoryList += DataPipeline._get_all_valid_recordings(new_path)

        directoryList = np.array(directoryList)
        np.random.shuffle(directoryList)
        return directoryList.tolist()
