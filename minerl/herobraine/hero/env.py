import json
import logging
import time
import xml.etree.ElementTree as ET
from typing import List, Tuple, Any, Dict

import MalmoPython
import gym
import numpy as np
from gym import error

from minerl.herobraine.hero.agent_handler import AgentHandler, HandlerCollection
from minerl.herobraine.hero.instance_manager import InstanceManager

RENDER_SIZE = (640, 480)

logger = logging.getLogger(__name__)
MAX_MISSION_RESET_WAIT_TIME = 60
MAX_MISSION_RESET_FALLBACK_TIMES = 3


# SINGLE_DIRECTION_DISCRETE_MOVEMENTS = [ "jumpeast", "jumpnorth", "jumpsouth", "jumpwest",
#                                         "movenorth", "moveeast", "movesouth", "movewest",
#                                         "jumpuse", "use", "attack", "jump" ]
#
# MULTIPLE_DIRECTION_DISCRETE_MOVEMENTS = [ "move", "turn", "look", "strafe",
#                                           "jumpmove", "jumpstrafe" ]

class HeroEnv(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self):
        super(HeroEnv, self).__init__()

        self.client_pool = None
        self.mc_process = None
        self.mission_spec = None
        self.observables = None
        self.actionables = None
        self.task_name = None
        self.max_retries = None
        self.agent_host = MalmoPython.AgentHost()

        self.screen = None
        self.finished = False
        self.first_time = True

    def init(self,
             inst: InstanceManager._Instance,
             mission_spec: MalmoPython.MissionSpec,
             observables: List[AgentHandler],
             actionables: List[AgentHandler],
             task_name: str,
             step_sleep=0.001, skip_steps=0, retry_sleep=2, max_retries=3, forceWorldReset=True):

        self.client_pool = inst.client_pool
        self.mission_spec = mission_spec
        self.observables = observables
        self.actionables = actionables
        self.task_name = task_name
        # pov observers

        self.last_image = None
        self.max_retries = max_retries
        self.forceWorldReset = forceWorldReset
        self.retry_sleep = retry_sleep
        self.step_sleep = step_sleep
        self.skip_steps = skip_steps
        self.mission_record_spec = MalmoPython.MissionRecordSpec()

    def deinit(self):
        self.client_pool = None
        self.mission_spec = None
        self.observables = None
        self.actionables = None

    def startMission(self):
        for retry in range(self.max_retries + 1):
            try:
                self.agent_host.startMission(self.mission_spec, self.client_pool, self.mission_record_spec, 0,
                                             self.task_name)
                break
            except RuntimeError as e:
                if retry == self.max_retries:
                    logger.critical("Error starting mission: " + str(e))
                    logger.critical("Too many attempts - giving up starting mission")
                    logger.debug("Mission XML sent to Malmo:")
                    logger.debug(self.mission_spec.getAsXML(True))
                    raise
                else:
                    logger.error("Error starting mission: " + str(e))
                    logger.debug("Sleeping for %d seconds...", self.retry_sleep)
                    time.sleep(self.retry_sleep)

    def reset(self):
        if not self.client_pool:
            raise RuntimeError("Environment not initialized with a client pool. "
                               "Try getting an instance from the instance manager")

        # force new world each time
        if self.forceWorldReset:
            self.mission_spec.forceWorldReset()

        # this seemed to increase probability of success in first try
        time.sleep(0.2)
        # Attempt to start a mission
        logger.info("Attempting to start mission...")
        self.startMission()

        # Loop until mission starts:
        logger.info("Waiting for the mission to start")
        time_passed = 0.0
        times_reset = 0
        world_state = self.agent_host.getWorldState()
        has_printed = False
        while not world_state.has_mission_begun:
            time.sleep(0.1)
            time_passed += 0.1
            world_state = self.agent_host.getWorldState()
            for error in world_state.errors:
                logger.warn(error.text)
            if (time_passed // 1) % 5 == 0 and not has_printed:
                has_printed = True
                logger.warn("Mission still hasn't started: {}".format(world_state))

            if time_passed > MAX_MISSION_RESET_WAIT_TIME:
                if times_reset < MAX_MISSION_RESET_FALLBACK_TIMES:
                    logger.warn("Mission start timed out. Trying to start again...")
                    self.startMission()
                    times_reset += 1
                raise RuntimeError("Timed out starting mission.")

        logger.log(35, "Mission running")
        self.last_frame = None
        self.frames = 0
        self.missed = 0
        self.last_observation = None
        logger.info("Getting the world state")
        _, frame, aux= self._get_world_state()
        logger.info("Got the world state")
        self.finished = False

        # process the video frame
        return HandlerCollection(self._get_observations(frame, aux))

    def _get_world_state(self):
        # wait till we have got at least one observation or mission has ended
        while True:
            # time.sleep(self.step_sleep)  # wait for 1ms to not consume entire CPU
            world_state = self.agent_host.peekWorldState()
            if world_state.number_of_observations_since_last_state > self.skip_steps or not world_state.is_mission_running or self.first_time:
                # For some reason number of observations since last state
                # remains 0, on first time you try to reset
                self.first_time = False
                break
        world_state = self.agent_host.getWorldState()

        # log errors and control messages
        for error in world_state.errors:
            logger.warn(error.text)
        for msg in world_state.mission_control_messages:
            # logger.debug(msg.text)
            root = ET.fromstring(msg.text)
            if root.tag == '{http://ProjectMalmo.microsoft.com}MissionEnded':
                print(msg.text)
                print(msg)
                for el in root.findall('{http://ProjectMalmo.microsoft.com}HumanReadableStatus'):
                    logger.info("Mission ended: %s", el.text)
        #See how many games were missed. This is useful for tuning mission max speeds.
        missed_obs = world_state.number_of_observations_since_last_state - len(world_state.observations) - self.skip_steps
        missed_video = world_state.number_of_video_frames_since_last_state <= 0
        self.frames += 1
        if (self.last_frame and missed_video) or (self.last_observation and missed_obs):
            self.missed += 1
        # process the video frame
        if world_state.number_of_video_frames_since_last_state > 0:
            assert len(world_state.video_frames) == 1
            self.last_frame = world_state.video_frames

        # Process the observation
        if world_state.number_of_observations_since_last_state > 0:
            assert len(world_state.observations) == 1
            self.last_observation = world_state.observations

        return world_state, self.last_frame, self.last_observation

    def _get_observations(self, frames, auxes) -> Dict[AgentHandler, Any]:
        hero_obs_dict = {}
        if frames:
            frame = frames[0]
            image = np.frombuffer(frame.pixels, dtype=np.uint8)
            image = image.reshape((frame.height, frame.width, frame.channels))
            hero_obs_dict["video"] = image

        if auxes:
            hero_obs_dict.update(json.loads(auxes[0].text))

        obs_dict = {
            obs_type: obs_type.from_hero(hero_obs_dict)
            for obs_type in self.observables
        }

        return obs_dict

    def step(self, action_col : Dict[AgentHandler, Any]) -> Tuple[HandlerCollection, float, bool, dict]:
        assert isinstance(action_col, dict) or isinstance(action_col, HandlerCollection), \
            "Stepping the hero env requires a dictionary of action handlers and their values.."
        # take the action only if mission is still running
        world_state = self.agent_host.peekWorldState()
        if world_state.is_mission_running:
            # take action
            cmds = [action_type.to_hero(action_col[action_type])
                    for action_type in action_col]
            # Join all of the commands with \n
            command = "\n".join(cmds)
            self.agent_host.sendCommand(command)
        # wait for the new state
        world_state, frames, auxes = self._get_world_state()

        # sum rewards (actually there should be only one)
        reward = 0
        for r in world_state.rewards:
            reward += r.getValue()
            # print(reward)

        # Get the state

        observations = self._get_observations(frames, auxes)
        observations = HandlerCollection(observations)
        # detect terminal state
        done = not world_state.is_mission_running

        if done and not self.finished:
            logger.debug("Agent missed \033[91m {0:0.02f}% \033[0m of frames or observations ".format(
                self.missed/self.frames*100))
            self.finished = True

        # other auxiliary data
        info = {
            'has_mission_begun': world_state.has_mission_begun,
            'is_mission_running': world_state.is_mission_running,
            'number_of_video_frames_since_last_state': world_state.number_of_video_frames_since_last_state,
            'number_of_rewards_since_last_state': world_state.number_of_rewards_since_last_state,
            'number_of_observations_since_last_state': world_state.number_of_observations_since_last_state,
            'mission_control_messages': [msg.text for msg in world_state.mission_control_messages]
        }

        return observations, reward, done, info

    def render(self, mode='human', close=False):
        if mode == 'rgb_array':
            return self.last_image
        # elif mode == 'human':
        #     try:
        #         import pygame
        #     except ImportError as e:
        #         raise error.DependencyNotInstalled("{}. (HINT: install pygame using `pip install pygame`".format(e))
        #
        #     if close:
        #         pygame.quit()
        #     else:
        #         if self.screen is None:
        #             pygame.init()
        #             self.screen = pygame.display.set_mode((640, 480))
        #         scaled_image = pygame.surfarray.make_surface(np.swapaxes(self._image, 0,1))
        #         # scaled_image = pygame.transform.scale(img, BIGGER_RENDER)
        #         self.screen.blit(scaled_image, (0, 0))
        #         pygame.event.get()
        #         pygame.display.update()
        else:
            raise error.UnsupportedMode("Unsupported render mode: " + mode)

    def close(self):
        self.deinit()

    def seed(self, seed=None):
        self.mission_spec.setWorldSeed(str(seed))
        return [seed]

    def pause(self):
        """
        Thanks daddy will @wguss
        """
        self.agent_host.sendCommand('pause 1')

    def unpause(self):
        """
        The balls in your court @wguss
        """
        self.agent_host.sendCommand('pause 0')
