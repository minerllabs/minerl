import json
import logging
import multiprocessing
import os
from collections import OrderedDict
from queue import PriorityQueue
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
        if max_sequence_len is not None and max_sequence_len > 1:
            raise NotImplementedError("Drawing batches of sequence is not supported")

        logger.info("Starting batch iterator on {}".format(self.data_dir))
        self.data_list = self._get_all_valid_recordings(self.data_dir)

        pool_size = self.size_to_dequeue * 4
        m = multiprocessing.Manager()
        data_queue = m.Queue(maxsize=self.size_to_dequeue // self.worker_batch_size * 4)

        # Setup arguments for the workers.
        files = [(file_dir, self.worker_batch_size, data_queue) for file_dir in self.data_list]
        map_promise = self.processing_pool.starmap_async(DataPipeline._load_data_pyfunc, files)

        # itterables = self.processing_pool.map_async(DataPipeline._generate_data_pyfunc, files)

        # Grab self.number_of_workers generators from the processing_pool
        # active_workers = itterables[:self.number_of_workers]


        random_queue = PriorityQueue(maxsize=pool_size)

        # We map the files -> load_data -> batch_pool -> random shuffle -> yield.
        start = 0
        incr = 0
        while not map_promise.ready() or not data_queue.empty() or not random_queue.empty():
            while not data_queue.empty() and not random_queue.full():
                for ex in data_queue.get():
                    if not random_queue.full():
                        r_num = np.random.rand(1)[0] * (1 - start) + start
                        random_queue.put(
                            (r_num, ex)
                        )
                        incr += 1
                        # print("d: {} r: {} rqput".format(data_queue.qsize(), random_queue.qsize()))
                    else:
                        break

            if incr > self.size_to_dequeue:
                if random_queue.qsize() < (batch_size):
                    if map_promise.ready():
                        break
                    else:
                        continue
                batch_with_incr = [random_queue.get() for _ in range(batch_size)]

                r1, batch = zip(*batch_with_incr)
                start = 0
                frame_batch, vector_batch = zip(*batch)

                # frame_batch = np.ones([batch_size, 64, 64])
                # vector_batch = np.ones([batch_size, 125])

                yield frame_batch, vector_batch

            # Move on to the next batch bool.
            # Todo: Move to a running pool, sampling as we enqueue. This is basically the random queue impl.
            # Todo: This will prevent the data from getting arbitrarily segmented.
            # batch_pool = []

            # TODO Release pre-shuffled dataset with no correlation between frames, sharded for runtime shuffling
            # TODO Release frame skip version of dataset with
        try:
            map_promise.get()
        except RuntimeError as e:
            logger.error("Failure in data pipeline: {}".format(e))

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
            logger.error("Starting worker!")

            # Start video decompression
            cap = cv2.VideoCapture(video_path)

            # Rendered State
            if vectorized:
                vec = np.load(numpy_path, mmap_mode='r', allow_pickle=False)
                num_states = vec.shape[0]
            else:
                vec = np.load(numpy_path, allow_pickle=False)
                num_states = vec['num_states']


            # Rendered Frames
            frame_skip = 0  # np.random.randint(0, len(univ)//2, 1)[0]
            frame_num = 0
            max_frame_num = num_states  # TODO: compute this from video metadata
            reset = False
            batches = []

            # Loop through the video and construct frames
            # of observations to be sent via the multiprocessing queue
            # in chunks of worker_batch_size to the batch_iter loop.

            # logger.error("Iterating through frames")
            for _ in range(num_states):
                ret, frame = cap.read()
                if frame_num < frame_skip:
                    frame_num += 1
                    continue

                if not ret or frame_num >= max_frame_num or frame_num > num_states:
                    # logger.info("ret is ", ret)
                    break
                else:
                    # We now construct a max_sequence_length sized batch.
                    if len(batches) >= worker_batch_size:
                        data_queue.put(batches)
                        batches = []

                    if reset:
                        batches = []
                        reset = False
                        pass
                    try:
                        # Construct a single observation object.
                        vf = (np.clip(frame[:, :, ::-1], 0, 255))
                        if vectorized:
                            uf = vec[frame_num]
                        else:
                            # for key in vec:
                            #     if isinstance(vec[key], np.ndarray):
                            #         if len(np.shape(vec[key])) > 1:
                            #             print(vec[key])
                            #         else:
                            #             print("bad key is ", key)
                            uf = {key: vec[key][frame_num] for key in vec.keys() if isinstance(vec[key], np.ndarray) and len(np.shape(vec[key])) > 1}

                        batches.append([vf, uf])

                    except Exception as e:
                        # If there is some error constructing the batch we just start a new sequence
                        # at the point that the exception was observed
                        logger.error("Exception \'{}\' caught in the middle of parsing \"{}\" in "
                                     "a worker of the data pipeline.".format(e, file_dir))
                        reset = True

                frame_num += 1

            logger.error("Finished")
            return batches

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
            if len([f for f in os.listdir(path) if f.endswith('.json')]) > 0:
                directoryList.append(path)

        for d in os.listdir(path):
            new_path = os.path.join(path, d)
            if os.path.isdir(new_path):
                directoryList += DataPipeline._get_all_valid_recordings(new_path)

        directoryList = np.array(directoryList)
        np.random.shuffle(directoryList)
        return directoryList.tolist()
