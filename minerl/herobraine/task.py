"""
task.py -- The main abstract implementation of tasks.
"""
import logging
import os
import sys
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Tuple, List

import MalmoPython
import gym
from gym import Space

import herobraine
from herobraine import hero

logger = logging.getLogger(__name__)


class Task(ABC):
    """
    A task is a Malmo environment with specific procedures
    and metrics that are recorded.
    """
    #Todo: Tasks should be able to subscribe to on episode completed!

    def __init__(self, name, env_spec):
        self.name = name
        self.__class__._uid = self.__class__._uid + 1 if hasattr(self.__class__, "_uid") else 1

        self.env_spec = env_spec
        self.mission_handlers = self.env_spec.create_mission_handlers()
        self.observables = self.env_spec.create_observables()
        self.actionables = self.env_spec.create_actionables()

        # Create the malmo mission
        self.mission_spec = self.setup_mission()
        self.mission_xml = ""

        # [For OpenAI Baselines]
        self.num_envs = 1

    def setup_mission(self) -> Tuple[MalmoPython.MissionSpec, Space, Space]:
        """
        Sets up the malmo mission.
        :return: The mission spec, observation, abd action space.
        """
        task_location = sys.modules[self.__module__].__file__
        mission_file_loc = os.path.realpath(os.path.abspath(
            os.path.join(os.path.dirname(task_location), self.get_mission_file())))

        logger.info("Loading mission from " + mission_file_loc)
        mission_xml = open(mission_file_loc, 'r').read()
        namespace = 'http://ProjectMalmo.microsoft.com'
        ET.register_namespace('', namespace)
        ET.register_namespace('xsi', "http://www.w3.org/2001/XMLSchema-instance")
        root = ET.fromstring(mission_xml)  # Type xml.etree.ElenementTree
        self.update_mission_xml(root, namespace)

        all_handlers = self.mission_handlers + self.observables + self.actionables
        for h in all_handlers:
            h.add_to_mission_xml(root, namespace)

        self.mission_xml = ET.tostring(root, encoding="UTF-8").decode('utf-8')
        mission_spec = MalmoPython.MissionSpec(self.mission_xml, True)
        logger.log(35, "Loaded mission: " + mission_spec.getSummary())

        # Gym-Minecraft originally removed all the command handlers
        # Instead, we will register different actionables and allow all commands by default.
        # For missions with custom command handlers, they need be added in the mission XML
        # and then registered in the given task's Task Task.create_actionables().
        # mission_spec.removeAllCommandHandlers()

        # Perform setup
        for h in all_handlers:
            h.add_to_mission_spec(mission_spec)

        return mission_spec

    @property
    def action_space(self):
        return gym.spaces.Tuple([a.space for a in self.actionables])

    @property
    def observation_space(self):
        return gym.spaces.Tuple([a.space for a in self.observables])

    @property
    def id(self) -> str:
        return "{}_{}".format(self.name, self.__class__._uid)

    def save(self, dir) -> None:
        writer = open(os.path.join(dir, 'modified_mission.xml'), 'w')
        writer.write(self.mission_xml)
        #return NotImplementedError

    def get_observables(self) -> List[herobraine.hero.AgentHandler]:
        return self.env_spec.create_observables()

    def get_actionables(self) -> List[herobraine.hero.AgentHandler]:
        return self.env_spec.create_actionables()

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        return self.env_spec.create_mission_handlers()

    #########################################
    #####      Abstract methods         #####
    #########################################

    @abstractmethod
    def get_filter(self, source):
        """
        Gets a filter for data from the universal action format.
        This filter is a herobraine.data.Pipe which converts
        the universal action format into the observation space and the action space.
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def get_mission_file(self) -> str:
        """
        Gets the mission file name of the task.
        :return:
        """
        raise NotImplementedError

    def update_mission_xml(self, etree: ET, ns: str) -> None:
        """
        Updates the mission xml
        :param etree: The root of the tree
        :param ns: The namespace of all elements
        """
        pass

