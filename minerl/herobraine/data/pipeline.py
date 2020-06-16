import json
import logging
import multiprocessing
import os
from collections import OrderedDict
from queue import PriorityQueue
from typing import List, Tuple, Any

import cv2
import numpy as np
from multiprocess.pool import Pool

from minerl.herobraine.hero.agent_handler import HandlerCollection, AgentHandler

logger = logging.getLogger(__name__)


class DataPipeline:
    """
    Creates a data pipeline.
    """

    def __init__(self,
                 observables: List[AgentHandler],
                 actionables: List[AgentHandler],
                 mission_handlers: List[AgentHandler],
                 data_directory,
                 num_workers,
                 worker_batch_size,
                 min_size_to_dequeue):
        """
        Sets up a tensorflow dataset to load videos from a given data directory.
        :param data_directory: the directory of the data to be loaded, eg: 'minerl.herobraine_parse/output/rendered/'
        """

        self.data_dir = data_directory
        self.observables = observables
        self.actionables = actionables
        self.mission_handlers = mission_handlers
        # self.vectorizer = vectorizer

        self.number_of_workers = num_workers
        self.worker_batch_size = worker_batch_size
        self.size_to_dequeue = min_size_to_dequeue
        self.processing_pool = Pool(self.number_of_workers)

    def batch_iter(self, batch_size, max_sequence_len):
        """
        Returns a generator for iterating through batches of the dataset.
        :param batch_size:
        :param max_sequence_len:
        :param number_of_workers:
        :param worker_batch_size:
        :param size_to_dequeue:
        :return:
        """
        logger.info("Starting batch iterator on {}".format(self.data_dir))
        self.data_list = self._get_all_valid_recordings(self.data_dir)

        pool_size = self.size_to_dequeue * 4
        m = multiprocessing.Manager()
        data_queue = m.Queue(maxsize=self.size_to_dequeue // self.worker_batch_size * 4)
        # Construct the arguments for the workers.
        files = [(d, self.observables, self.actionables, self.mission_handlers,
                  max_sequence_len, self.worker_batch_size, data_queue)
                 for d in self.data_list]

        random_queue = PriorityQueue(maxsize=pool_size)

        map_promise = self.processing_pool.map_async(DataPipeline._load_data_pyfunc, files)

        # We map the files -> load_data -> batch_pool -> random shuffle -> yield.
        # batch_pool = []
        start = 0
        incr = 0
        while not map_promise.ready() or not data_queue.empty() or not random_queue.empty():
            # if not map_promise.ready() and data_queue.empty() and random_queue.qsize() < 32:
            # print("mp: {} d: {} r: {}".format(map_promise.ready(), data_queue.qsize(), random_queue.qsize()))

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
                traj_obs, traj_acts, traj_handlers = zip(*batch)

                observation_batch = HandlerCollection({
                    o: np.asarray([
                        traj_ob[i] for traj_ob in traj_obs
                    ])
                    for i, o in enumerate(self.observables)
                })
                action_batch = HandlerCollection({
                    a: np.asarray([
                        traj_act[i] for traj_act in traj_acts
                    ])
                    for i, a in enumerate(self.actionables)
                })

                mission_handler_batch = HandlerCollection({
                    m: np.asarray([
                        traj_handler[i] for traj_handler in traj_handlers
                    ])
                    for i, m in enumerate(self.mission_handlers)
                })
                yield observation_batch, action_batch, mission_handler_batch
            # Move on to the next batch bool.
            # Todo: Move to a running pool, sampling as we enqueue. This is basically the random queue impl.
            # Todo: This will prevent the data from getting arbitrarily segmented.
            # batch_pool = []
        try:
            map_promise.get()
        except RuntimeError as e:
            logger.error("Failure in data pipeline: {}".format(e))

        logger.info("Epoch complete.")

    ############################
    ## PRIVATE METHODS
    #############################

    # Todo: Make data pipeline split files per push.
    @staticmethod
    def _load_data_pyfunc(
            args: Tuple[Any, List[AgentHandler], List[AgentHandler], List[AgentHandler], int, int, Any], ):
        """
        Loads a action trajectory from a given file and incrementally yields via a data_queue.
        :param args:
        :return:
        """

        # Get the initial directories for the data queue.
        inst_dir, observables, actionables, mission_handlers, max_seq_len, worker_batch_size, data_queue = args
        # logger.warning(inst_dir)
        recording_path = str(os.path.join(inst_dir, 'recording.mp4'))
        univ_path = str(os.path.join(inst_dir, 'univ.json'))

        try:
            # logger.error("Starting worker!")
            cap = cv2.VideoCapture(recording_path)
            # Litty uni
            with open(univ_path, 'r') as f:
                univ = {int(k): v for (k, v) in (json.load(f)).items()}
                univ = OrderedDict(univ)
                univ = np.array(list(univ.values()))

            # Litty viddy
            frame_skip = 0  # np.random.randint(0, len(univ)//2, 1)[0]
            frame_num = 0
            reset = True
            batches = []

            # Loop through the video and construct frames
            # of observations to be sent via the multiprocessing queue
            # in chunks of worker_batch_size to the batch_iter loop.

            # logger.error("Iterating through frames")
            for _ in range(len(univ)):
                ret, frame = cap.read()
                if frame_num <= frame_skip:
                    frame_num += 1
                    continue

                if not ret or frame_num >= len(univ):
                    break
                else:
                    # We now construct a max_sequence_length sized batch.
                    if len(batches) >= worker_batch_size:
                        data_queue.put(batches)
                        batches = []

                    if reset:
                        observation_datastream = [[] for _ in observables]
                        action_datastream = [[] for _ in actionables]
                        mhandler_datastream = [[] for _ in mission_handlers]
                    try:

                        # Construct a single observation object.
                        vf = (np.clip(frame[:, :, ::-1], 0, 255))
                        uf = univ[frame_num]

                        frame = {'pov': vf}
                        frame.update(uf)

                        for i, o in enumerate(observables):
                            observation_datastream[i].append(o.from_universal(frame))

                        for i, a in enumerate(actionables):
                            action_datastream[i].append(a.from_universal(frame))

                        for i, m in enumerate(mission_handlers):
                            try:
                                mhandler_datastream[i].append(m.from_universal(frame))
                            except NotImplementedError:
                                # Not all mission handlers can be extracted from files
                                # This is okay as they are intended to be auxiliary handlers
                                mhandler_datastream[i].append(None)
                                pass

                        if len(observation_datastream[0]) == max_seq_len:
                            observation_datastream = [np.asarray(np.clip(o, 0, 255)) for o in observation_datastream]
                            action_datastream = [np.asarray(np.clip(a, 0, 255)) for a in action_datastream]

                            reset = True
                            batches.append((observation_datastream, action_datastream, mhandler_datastream))
                    except Exception as e:
                        # If there is some error constructing the batch we just start a new sequence
                        # at the point that the exception was observed
                        logger.warn("Exception {} caught in the middle of parsing {} in "
                                    "a worker of the data pipeline.".format(e, inst_dir))
                        reset = True

                frame_num += 1

            # logger.error("Finished")
            return batches

        except Exception as e:
            logger.error("Caught Exception")
            return None

        # logger.error("Finished")
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
