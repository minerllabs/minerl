from abc import abstractmethod
from typing import List

import jinja2
from minerl.herobraine.hero.agent_handler import AgentHandler
from minerl.env.spaces import Dict
# import minerl.env.spaces as spaces
import gym
import os
import abc

MISSION_TEMPLATE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'hero', 'mission.xml.j2')
from minerl.herobraine.hero import spaces

# TODO (R): Rename to Task
class EnvSpec(abc.ABC):
    ENTRYPOINT = 'minerl.env:MineRLEnv'

    def __init__(self, name, max_episode_steps=None, reward_threshold=None):
        self.name = name
        self.max_episode_steps = max_episode_steps
        self.reward_threshold = reward_threshold

        self.observables = self.create_observables()
        self.actionables = self.create_actionables()
        self.rewardables = self.create_rewardables() 
        self.agent_handlers = self.create_agent_handlers()


        self.server_initial_conditions = sefl.create_server_initial_conditions()
        self.server_handlers = self.create_server_handlers()

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
    def create_observables(self) -> List[AgentHandler]:
        """Specifies all of the observation handlers for the env specification.
        These are used to comprise the observation space.
        """
        raise NotImplementedError('subclasses must override create_observables()!')

    # actionables
    @abstractmethod
    def create_actionables(self) -> List[AgentHandler]:
        """Specifies all of the action handlers for the env specification.
        These are used to comprise the action space.
        """
        raise NotImplementedError('subclasses must override create_actionables()!')

    # rewardables
    @abstractmethod
    def create_rewardables(self) -> List[AgentHandler]:
        """Specifies all of the reward handlers for the env specification.
        These are used to comprise the reward and are summed in the gym environment.
        """
        raise NotImplementedError('subclasses must override create_rewardables()!')

    
    @abstractmethod
    def create_agent_handlers(self) -> List[AgentHandler]:
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
    def create_server_handlers(self) -> List[AgentHandler]:
         raise NotImplementedError('subclasses must override create_server_handlers()!')


    @abstractmethod
    def create_server_initial_conditions(self) -> List[AgentHandler]:
        raise  NotImplementedError('subclasses must override create_server_initial_conditions()!')


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

    def register(self):
        reg_spec = dict(
            id=self.name,
            entry_point=EnvSpec.ENTRYPOINT,
            kwargs={
                'observation_space': self.observation_space,
                'action_space': self.action_space,
                'docstr': self.get_docstring(),
                'xml': os.path.join(MISSIONS_DIR, self.xml),
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
    @property
    def to_xml(self) -> str:
        """Gets the XML by templating mission.xml.j2 using Jinja
        """
        with open(MISSION_TEMPLATE, "rt") as fh:
            template = jinja2.Template(fh.read())
            xml = template.render((self).__dict__)
        return xml
            
        