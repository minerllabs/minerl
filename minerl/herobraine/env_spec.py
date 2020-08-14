# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

from abc import abstractmethod
from minerl.herobraine.hero.spaces import Dict
from minerl.herobraine.hero.handler import Handler
from typing import List

import jinja2
import gym
from lxml import etree
import os
import abc

MISSION_TEMPLATE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'hero', 'mission.xml.j2')
from minerl.herobraine.hero import spaces

# TODO (R): Rename to Task
class EnvSpec(abc.ABC):
    ENTRYPOINT = 'minerl.env:MineRLEnv'
    FAKE_ENTRYPOINT = 'minerl.env:FakeMineRLEnv'

    def __init__(self, name, max_episode_steps=None, reward_threshold=None):
        self.name = name
        self.max_episode_steps = max_episode_steps
        self.reward_threshold = reward_threshold

        self.reset()

    def reset(self):
        self.observables = self.create_observables()
        self.actionables = self.create_actionables()
        self.rewardables = self.create_rewardables() 
        self.agent_handlers = self.create_agent_handlers()
        self.agent_start = self.create_agent_start()

       
        self.server_initial_conditions = self.create_server_initial_conditions()
        self.server_world_generators = self.create_server_world_generators()
        self.server_decorators = self.create_server_decorators()
        self.server_quit_producers = self.create_server_quit_producers()
        # self.monitors = []

        # check that the observables (list) have no duplicate to_strings
        assert len([o.to_string() for o in self.observables]) == len(set([o.to_string() for o in self.observables]))
        assert len([a.to_string() for a in self.actionables]) == len(set([a.to_string() for a in self.actionables]))


        self._observation_space = self.create_observation_space()
        self._action_space = self.create_action_space()
    
    ########################
    ### API METHODS #######
    #######################


    ############## AGENT ##########################
    
    # observables
    @abstractmethod
    def create_observables(self) -> List[Handler]:
        """Specifies all of the observation handlers for the env specification.
        These are used to comprise the observation space.
        """
        raise NotImplementedError('subclasses must override create_observables()!')

    # actionables
    @abstractmethod
    def create_actionables(self) -> List[Handler]:
        """Specifies all of the action handlers for the env specification.
        These are used to comprise the action space.
        """
        raise NotImplementedError('subclasses must override create_actionables()!')

    # rewardables
    @abstractmethod
    def create_rewardables(self) -> List[Handler]:
        """Specifies all of the reward handlers for the env specification.
        These are used to comprise the reward and are summed in the gym environment.
        """
        raise NotImplementedError('subclasses must override create_rewardables()!')

    @abstractmethod
    def create_agent_start(self) -> List[Handler]:
        """Specifies all fo the handlers which constitute the agents initial inventory etc
        at the beginning of a mission. This can be used for domain randomization
        as these handlers are reinstantiated on every reset!
        """
        raise  NotImplementedError('subclasses must override create_agent_start()!')

    
    @abstractmethod
    def create_agent_handlers(self) -> List[Handler]:
        """Creates all of the agent handlers for an env specificaiton.
        These generally are used to specify agent specific behaviours that don't
        directly correspond to rewards/actions/observaitons.

        For example, one can specify all those behaviours which terminate a mission:
            AgentQuitFrom... Handler, etc.

        Raises:
            NotImplementedError: [description]

        Returns:
            List[AgentHandler]: [description]
        """
        raise NotImplementedError('subclasses must override create_agent_handlers()!')


    # monitors TODO (R):
    # @abstractmethod
    # def create_monitors(self) -> List[AgentHandler]:
    #     """Specifies all of the environment monitor handlers for the env specification.
    #     These are used to comprise the reward and are summed in the gym environment.
    #     """
    #     raise NotImplementedError('subclasses must override create_monitors()!')


    ##################### SERVER #########################

    @abstractmethod
    def create_server_initial_conditions(self) -> List[Handler]:
        raise  NotImplementedError('subclasses must override create_server_initial_conditions()!')

    @abstractmethod
    def create_server_decorators(self) -> List[Handler]:     
        raise NotImplementedError('subclasses must override create_server_decorators()!')   
    
    @abstractmethod     
    def create_server_world_generators(self) -> List[Handler]:     
        raise NotImplementedError('subclasses must override create_server_world_generators()!')       
    
    @abstractmethod     
    def create_server_quit_producers(self) -> List[Handler]:     
        raise NotImplementedError('subclasses must override create_server_quit_producers()!')       
    

    ################## PROPERTIES & HELPERS #################
    @property
    def observation_space(self) -> Dict:
        return self._observation_space

    @property
    def action_space(self) -> Dict:
        return self._action_space

    def to_string(self):
        return self.name

    @abstractmethod
    def is_from_folder(self, folder: str) -> bool:
        raise NotImplementedError('subclasses must override is_from_folder()!')

    @abstractmethod
    def determine_success_from_rewards(self, rewards: list) -> bool:
        # TODO: 
        raise NotImplementedError('subclasses must override determine_success_from_rewards()')

    def create_observation_space(self):
        # Todo: handle nested dict space.
        return spaces.Dict({
            o.to_string(): o.space for o in self.observables
        })

    def create_action_space(self):
        return spaces.Dict({
            a.to_string(): a.space for a in self.actionables
        })

    @abstractmethod
    def get_docstring(self):
        return NotImplemented

    def register(self, fake=False):
        reg_spec = dict(
            id=("Fake" if fake else "") + self.name,
            entry_point=EnvSpec.ENTRYPOINT if not fake else EnvSpec.FAKE_ENTRYPOINT,
            kwargs={
                'observation_space': self.observation_space,
                'action_space': self.action_space,
                'docstr': self.get_docstring(),
                'xml': self.to_xml(),
                'env_spec': self,
            },
            max_episode_steps=self.max_episode_steps,
        )
        if self.reward_threshold:
            reg_spec.update(dict(reward_threshold=self.reward_threshold))

        gym.register(**reg_spec)

    def __repr__(self):
        """
        Prints the class, name, observation space, and action space of the handler.
        """
        return '{}-{}-spaces({},{})'.format(self.__class__.__name__, self.name, self.observation_space,
                                            self.action_space)

    def to_xml(self) -> str:
        """Gets the XML by templating mission.xml.j2 using Jinja
        """
        with open(MISSION_TEMPLATE, "rt") as fh:
            # TODO: Pull this out into a method.
            var_dict = {}
            for attr_name in dir(self):
                if 'to_xml' not in attr_name:
                    var_dict[attr_name] = getattr(self, attr_name)

            env = jinja2.Environment(undefined=jinja2.StrictUndefined)
            template = env.from_string(fh.read())
            xml = template.render(var_dict)

        # Now do one more pretty printing
        
        xml = etree.tostring(etree.fromstring(xml.encode('utf-8')), pretty_print=True).decode('utf-8')
        # TODO: Perhaps some logging is necessary
        # print(xml)
        return xml
            
    def get_consolidated_xml(self, handlers : List[Handler]) -> List[str]:
        """Consolidates duplicate XML representations from the handlers.

        Deduplication happens by first getting all of the handler.xml() strings
        of the handlers, and then converting them into etrees. After that we check 
        if the there are any top level elements that are duplicated and pick the first of them
        to retain. We then convert the remaining etrees back into strings and join them with new lines.

        Args:
            handlers (List[Handler]): A list of handlers to consolidate.

        Returns:
            str: The XML
        """
        handler_xml_strs = [handler.xml() for handler in handlers]

        
        if not handler_xml_strs:
            return ''

        # TODO: RAISE VALID XML ERROR. FOR EASE OF USE
        trees = [etree.fromstring(xml) for xml in handler_xml_strs]
        consolidated_trees = {tree.tag: tree for tree in trees}.values()
        
        

        return [etree.tostring(t, pretty_print=True).decode('utf-8')  
            for t in consolidated_trees]


