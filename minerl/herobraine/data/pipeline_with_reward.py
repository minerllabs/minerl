# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton


# TODO: DEPRECRATE.
import json
import logging
import multiprocessing
import os
from collections import OrderedDict
from queue import Queue, PriorityQueue
from typing import List, Tuple, Any

import cv2
import numpy as np
from multiprocess.pool import Pool

from minerl.herobraine.hero.agent_handler import HandlerCollection, AgentHandler
from minerl.herobraine.hero.handlers import RewardHandler

logger = logging.getLogger(__name__)


class DataPipelineWithReward:
    """
    Creates a data pipeline that also outputs discounted reward.
    """

    def __init__(self,
                 observables: List[AgentHandler],
                 actionables: List[AgentHandler],
                 mission_handlers: List[AgentHandler],
                 nsteps,
                 gamma,
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
        self.nsteps = nsteps
        self.gamma = gamma

        self.processing_pool = Pool(self.number_of_workers)
        self.m = multiprocessing.Manager()
        self.data_queue = self.m.Queue(maxsize=self.size_to_dequeue // self.worker_batch_size * 4)

        pool_size = self.size_to_dequeue * 4
        self.random_queue = PriorityQueue(maxsize=pool_size)

    def batch_iter(self, batch_size):
        """
        Returns a generator for iterating through batches of the dataset.
        :param batch_size:
        :param number_of_workers:
        :param worker_batch_size:
        :param size_to_dequeue:
        :return:
        """
        logger.info("Starting batch iterator on {}".format(self.data_dir))
        data_list = self._get_all_valid_recordings(self.data_dir)

        load_data_func = self._get_load_data_func(self.data_queue, self.nsteps,
                                                  self.worker_batch_size, self.mission_handlers,
                                                  self.observables, self.actionables,
                                                  self.gamma)
        map_promise = self.processing_pool.map_async(load_data_func, data_list)

        # We map the files -> load_data -> batch_pool -> random shuffle -> yield.
        # batch_pool = []
        start = 0
        incr = 0
        while not map_promise.ready() or not self.data_queue.empty() or not self.random_queue.empty():
            # print("d: {} r: {}".format(data_queue.qsize(), random_queue.qsize()))

            while not self.data_queue.empty() and not self.random_queue.full():
                for ex in self.data_queue.get():
                    if not self.random_queue.full():
                        r_num = np.random.rand(1)[0] * (1 - start) + start
                        self.random_queue.put(
                            (r_num, ex)
                        )
                        incr += 1
                        # print("d: {} r: {} rqput".format(data_queue.qsize(), random_queue.qsize()))
                    else:
                        break

            if incr > self.size_to_dequeue:
                if self.random_queue.qsize() < (batch_size):
                    if map_promise.ready():
                        break
                    else:
                        continue
                batch_with_incr = [self.random_queue.get() for _ in range(batch_size)]

                r1, batch = zip(*batch_with_incr)
                start = 0
                traj_obs, traj_acts, traj_handlers, traj_n_obs, discounted_rewards, elapsed = zip(*batch)

                observation_batch = [
                    HandlerCollection({
                        o: np.asarray(traj_ob[i]) for i, o in enumerate(self.observables)
                    }) for traj_ob in traj_obs
                ]
                action_batch = [
                    HandlerCollection({
                        a: np.asarray(traj_act[i]) for i, a in enumerate(self.actionables)
                    }) for traj_act in traj_acts
                ]
                mission_handler_batch = [
                    HandlerCollection({
                        m: np.asarray(traj_handler[i]) for i, m in enumerate(self.mission_handlers)
                    }) for traj_handler in traj_handlers
                ]
                next_observation_batch = [
                    HandlerCollection({
                        o: np.asarray(traj_n_ob[i]) for i, o in enumerate(self.observables)
                    }) for traj_n_ob in traj_n_obs
                ]
                yield observation_batch, action_batch, mission_handler_batch, next_observation_batch, discounted_rewards, elapsed
            # Move on to the next batch bool.
            # Todo: Move to a running pool, sampling as we enqueue. This is basically the random queue impl.
            # Todo: This will prevent the data from getting arbitrarily segmented.
            # batch_pool = []
        try:
            map_promise.get()
        except RuntimeError as e:
            logger.error("Failure in data pipeline: {}".format(e))

        logger.info("Epoch complete.")

    def close(self):
        self.processing_pool.close()
        self.processing_pool.join()

    ############################
    ## PRIVATE METHODS
    #############################

    @staticmethod
    def _get_load_data_func(data_queue, nsteps, worker_batch_size, mission_handlers,
                            observables, actionables, gamma):
        def _load_data(inst_dir):
            recording_path = str(os.path.join(inst_dir, 'recording.mp4'))
            univ_path = str(os.path.join(inst_dir, 'univ.json'))

            try:
                cap = cv2.VideoCapture(recording_path)
                # Litty uni
                with open(univ_path, 'r') as f:
                    univ = {int(k): v for (k, v) in (json.load(f)).items()}
                    univ = OrderedDict(univ)
                    univ = np.array(list(univ.values()))

                # Litty viddy
                batches = []
                rewards = []
                frames_queue = Queue(maxsize=nsteps)

                # Loop through the video and construct frames
                # of observations to be sent via the multiprocessing queue
                # in chunks of worker_batch_size to the batch_iter loop.
                frame_num = 0
                while True:
                    ret, frame = cap.read()

                    if not ret or frame_num >= len(univ):
                        break
                    else:
                        # print("Batches {} and worker batch size {}".format(len(batches), self.worker_batch_size))
                        if len(batches) >= worker_batch_size:
                            data_queue.put(batches)
                            batches = []

                        try:
                            # Construct a single observation object.
                            vf = (np.clip(frame[:, :, ::-1], 0, 255))
                            uf = univ[frame_num]

                            frame = {'pov': vf}
                            frame.update(uf)

                            cur_reward = 0
                            for m in mission_handlers:
                                try:
                                    if isinstance(m, RewardHandler):
                                        cur_reward += m.from_universal(frame)
                                except NotImplementedError:
                                    pass
                            rewards.append(cur_reward)

                            # print("Frames queue size {}".format(frames_queue.qsize()))
                            frames_queue.put(frame)
                            if frames_queue.full():
                                next_obs = [o.from_universal(frame) for o in observables]
                                frame = frames_queue.get()
                                obs = [o.from_universal(frame) for o in observables]
                                act = [a.from_universal(frame) for a in actionables]
                                mission = []
                                for m in mission_handlers:
                                    try:
                                        mission.append(m.from_universal(frame))
                                    except NotImplementedError:
                                        mission.append(None)
                                        pass

                                batches.append((obs, act, mission, next_obs,
                                                DataPipelineWithReward._calculate_discount_rew(rewards[-nsteps:],
                                                                                               gamma),
                                                frame_num + 1 - nsteps))
                        except Exception as e:
                            # If there is some error constructing the batch we just start a new sequence
                            # at the point that the exception was observed
                            logger.warn("Exception {} caught in the middle of parsing {} in "
                                        "a worker of the data pipeline.".format(e, inst_dir))

                    frame_num += 1

                return batches
            except Exception as e:
                logger.error("Caught Exception")
                raise e
                return None

        return _load_data

    @staticmethod
    def _calculate_discount_rew(rewards, gamma):
        total_reward = 0
        for i, rew in enumerate(rewards):
            total_reward += (gamma ** i) * rew
        return total_reward

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
                directoryList += DataPipelineWithReward._get_all_valid_recordings(new_path)

        directoryList = np.array(directoryList)
        np.random.shuffle(directoryList)
        return directoryList.tolist()
