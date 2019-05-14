import json
import logging
import multiprocessing
import os
import time
from collections import OrderedDict
from queue import PriorityQueue, Empty
from typing import List, Tuple, Any
from itertools import cycle, islice

import cv2
import os
import numpy as np

logger = logging.getLogger(__name__)


class DataPipeline:
    """
    Creates a data pipeline.
    """

    def __init__(self,
                 data_directory: os.path,
                 num_workers: int,
                 worker_batch_size: int,
                 min_size_to_dequeue: int):
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
        """

        self.data_dir = data_directory

        self.number_of_workers = num_workers
        self.worker_batch_size = worker_batch_size
        self.size_to_dequeue = min_size_to_dequeue
        self.processing_pool = multiprocessing.Pool(self.number_of_workers)

    def batch_iter(self, batch_size: int, max_sequence_len=None):
        """
        Returns a generator for iterating through batches of the dataset.
        :param batch_size:
        :param max_sequence_len:
        :return:
        """
        if max_sequence_len is not None:
            raise NotImplementedError("Drawing batches of consecutive frames is not supported yet")

        logger.info("Starting batch iterator on {}".format(self.data_dir))
        self.data_list = self._get_all_valid_recordings(self.data_dir)

        pool_size = self.size_to_dequeue * 4
        m = multiprocessing.Manager()
        data_queue = m.Queue(maxsize=self.size_to_dequeue * self.worker_batch_size * 4)
        data_queue = m.Queue(maxsize=self.worker_batch_size * 1000)

        # Setup arguments for the workers.
        files = [(file_dir, self.worker_batch_size, data_queue) for file_dir in self.data_list]
        map_promise = self.processing_pool.starmap_async(DataPipeline._load_data_pyfunc, files)

        # iterables = self.processing_pool.map_async(DataPipeline._generate_data_pyfunc, files)

        # Grab self.number_of_workers generators from the processing_pool
        # active_workers = iterables[:self.number_of_workers]

        random_queue = PriorityQueue(maxsize=pool_size)

        # We map the files -> load_data -> batch_pool -> random shuffle -> yield.
        start = 0
        incr = 0

        while True:
            try:
                sequence = data_queue.get_nowait()
                action_batch, frame_batch, reward_batch = sequence
                yield action_batch, frame_batch, reward_batch
            except Empty:
                time.sleep(0.1)

        while not map_promise.ready() or not data_queue.empty() or not random_queue.empty():
            while not data_queue.empty() and not random_queue.full():
                sequence = data_queue.get()
                # for ex in data_queue.get():
                # print(len(ex))
                # print([len(x  ) for x in ex])
                # print([x.shape for x in ex])
                action_batch, frame_batch, reward_batch = sequence

                # frame_batch = np.ones([batch_size, 64, 64])
                # vector_batch = np.ones([batch_size, 125])

                yield action_batch, frame_batch, reward_batch
            #         if not random_queue.full():
            #             r_num = np.random.rand(1)[0] * (1 - start) + start
            #             random_queue.put(
            #                 (r_num, ex)
            #             )
            #             incr += 1
            #             # print("d: {} r: {} rqput".format(data_queue.qsize(), random_queue.qsize()))
            #         else:
            #             break
            #
            # if incr > self.size_to_dequeue:
            #     if random_queue.qsize() < (batch_size):
            #         if map_promise.ready():
            #             break
            #         else:
            #             continue
            #     batch_with_incr = [random_queue.get() for _ in range(batch_size)]
            #
            #     r1, batch = zip(*batch_with_incr)
            #     start = 0
            #     action_batch, frame_batch, reward_batch = zip(*batch)
            #
            #     # frame_batch = np.ones([batch_size, 64, 64])
            #     # vector_batch = np.ones([batch_size, 125])
            #
            #     yield action_batch, frame_batch, reward_batch
            #
            # # Move on to the next batch bool.
            # # Todo: Move to a running pool, sampling as we enqueue. This is basically the random queue impl.
            # # Todo: This will prevent the data from getting arbitrarily segmented.
            # # batch_pool = []
            #
            # # TODO Release pre-shuffled dataset with no correlation between frames, sharded for runtime shuffling
            # # TODO Release frame skip version of dataset with
        # try:
        #     map_promise.get()
        # except RuntimeError as e:
        #     logger.error("Failure in data pipeline: {}".format(e))

        logger.info("Epoch complete.")

    ############################
    ## PRIVATE METHODS
    #############################

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
    def _load_data_pyfunc(file_dir: str, worker_batch_size: int, data_queue, vectorized=False, skip_interval=0):
        """
        Enqueueing mechanism for loading a trajectory from a file onto the data_queue
        :param file_dir: file path to data directory
        :param skip_interval: Number of time steps to skip between each sample
        :param worker_batch_size: Number of time steps in each enqueued batch
        :param data_queue: multiprocessing data queue
        :return:
        """

        # logger.warning(inst_dir)
        video_path = str(os.path.join(file_dir, 'recording.mp4'))
        if vectorized:
            numpy_path = str(os.path.join(file_dir, 'rendered.npy'))
        else:
            numpy_path = str(os.path.join(file_dir, 'rendered.npz'))


        try:
            # logger.error("Starting worker!")

            # Start video decompression
            cap = cv2.VideoCapture(video_path)

            # Load numpy file
            state = np.load(numpy_path, allow_pickle=True)

            action_dict = {key: state[key] for key in state if key.startswith('action_')}
            reward_vec = state['reward']
            info_dict = {key: state[key] for key in state if key.startswith('observation_')}

            num_states = len(reward_vec)


            # Rendered State
                # print("Loading npz file: ", numpy_path)
                # print(state)
                # print([a for a in state])
                # print([state[a] for a in state])
                # [action_vec, reward_vec, info_vec] = np.l oad(numpy_path, allow_pickle=False)
                # print('Action:', [(key[len('action_'):], state[key]) for key in state if key.startswith('action_')])
                # print('Reward:', state['reward'])
                # print('min:', min(state['reward']), 'max:', max(state['reward']))
                # print('Info', [(key[len('observation_'):], state[key]) for key in state if key != 'action' and key != 'reward'])

                # action_dict = {key[len('action_'):]: state[key] for key in state if key.startswith('action_')}
                # reward_vec = state['reward']
                # info_dict = {key[len('observation_'):]: state[key] for key in state if key.startswith('observation_')}
                # print("Found", num_states, "states")

            # Rendered Frames
            frame_skip = 0  # np.random.randint(0, len(univ)//2, 1)[0]
            frame_num = 0
            max_seq_len = 1
            max_frame_num = num_states  # TODO: compute this with min over frames from video metadata
            reset = True
            batches = []
            observables = list(info_dict.keys()).copy()
            observables.append('pov') # TODO remove maybe
            actionables = list(action_dict.keys())
            mission_handlers = ['reward']

            # Loop through the video and construct frames
            # of observations to be sent via the multiprocessing queue
            # in chunks of worker_batch_size to the batch_iter loop.
            while True:
                ret = True
                frames = []
                start_idx = frame_num

                # Collect up to worker_batch_size number of frames
                try:
                    while ret and frame_num < max_frame_num and frame_num < num_states and len(frames) < worker_batch_size:
                        ret, frame = cap.read()
                        if ret:
                            frames.append(np.asarray(np.clip(frame, 0, 255), dtype=np.uint8))
                            frame_num += 1
                except Exception as err:
                    print("error reading capture device:", err)
                    # print('Is it early with no frames:', frame_num, max_frame_num, num_states, len(frames), worker_batch_size)
                    raise err

                if len(frames) == 0:
                    break

                stop_idx = start_idx + len(frames)
                # print('Num frames in batch:', stop_idx - start_idx)

                # Load non-image data from npz
                observation_data = [None for _ in observables]
                action_data = [None for _ in actionables]
                reward_data = None

                try:
                    for i, key in enumerate(observables):
                        if key == 'pov':
                            observation_data[i] = np.asanyarray(frames)
                        else:
                            observation_data[i] = np.asanyarray(state[key][start_idx:stop_idx])

                    for i, key in enumerate(actionables):
                        action_data[i] = np.asanyarray(state[key][start_idx:stop_idx])

                    reward_data = np.asanyarray(reward_vec[start_idx:stop_idx], dtype=np.float32)
                except Exception as err:
                    print("error drawing batch from npz file:", err)
                    raise err
                # print(type(observation_data))
                # print(type(action_data))
                # print(type(reward_data))

                # batches = tuple((action_data, observation_data, reward_data))
                batches = [action_data, observation_data, [reward_data]]

                # print('we put')
                # print(type(batches))
                # print(len(batches))
                # print([len(x) for x in batches])
                #
                # print('and then')

                # print('Action', action_data)
                # print('Observation', observation_data)
                # print('Reward', reward_data.shape, reward_data)
                # time.sleep(0.1)
                data_queue.put(batches)

                    if reset:
                        observation_datastream = [[] for _ in observables]
                        action_datastream = [[] for _ in actionables]
                        mhandler_datastream = [[] for _ in mission_handlers]
                    try:

                        for i, o in enumerate(observables):
                            if o == 'pov':
                                observation_datastream[i].append(np.clip(frame[:, :, ::-1], 0, 255))
                            else:
                                print(o, type(state[o][frame_num]))
                                observation_datastream[i].append(state[o][frame_num])

                        for i, a in enumerate(actionables):
                            print(a, type(state[a][frame_num]))
                            action_datastream[i].append(state[a][frame_num])

                        for i, m in enumerate(mission_handlers):
                            try:
                                print(m, type(state[m][frame_num]))
                                mhandler_datastream[i].append(state[m][frame_num])
                            except KeyError:
                                # Not all mission handlers can be extracted from files
                                # This is okay as they are intended to be auxiliary handlers
                                mhandler_datastream[i].append(None)
                                pass

                if not ret:
                    break

            # logger.error("Finished")
            return None
        except WindowsError as e:
            logger.info("Caught windows error - this is expected when closing the data pool")
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
