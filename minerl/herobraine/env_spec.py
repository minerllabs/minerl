# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

from abc import abstractmethod
from minerl.herobraine.hero.handlers.translation import TranslationHandler
import typing
from minerl.herobraine.hero.spaces import Dict
from minerl.herobraine.hero.handler import Handler
from typing import List, Optional

import jinja2
import gym
from lxml import etree
import os
import abc
import importlib

MISSION_TEMPLATE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'hero', 'mission.xml.j2')
from minerl.herobraine.hero import spaces


class EnvSpec(abc.ABC):
    U_MULTI_AGENT_ENTRYPOINT = 'minerl.env._multiagent:_MultiAgentEnv'
    U_FAKE_MULTI_AGENT_ENTRYPOINT = 'minerl.env._fake:_FakeMultiAgentEnv'
    U_SINGLE_AGENT_ENTRYPOINT = 'minerl.env._singleagent:_SingleAgentEnv'
    U_FAKE_SINGLE_AGENT_ENTRYPOINT = 'minerl.env._fake:_FakeSingleAgentEnv'

    def __init__(self, name, max_episode_steps=None, reward_threshold=None, agent_count=None):
        self.name = name
        self.max_episode_steps = max_episode_steps
        self.reward_threshold = reward_threshold
        self.agent_count = 1 if agent_count is None else agent_count
        self.is_single_agent = agent_count is None
        self.agent_names = ["agent_{role}".format(role=role) for role in range(self.agent_count)]

        self.reset()

    def reset(self):
        # Note: currently only agent_start needs to be per-agent. To make more attributes per-agent,
        # remember to modify minerl/herobraine/hero/mission.xml.j2 as well.
        self.observables = self.create_observables()
        self.actionables = self.create_actionables()
        self.rewardables = self.create_rewardables()
        self.agent_handlers = self.create_agent_handlers()
        self.monitors = self.create_monitors()

        self.server_initial_conditions = self.create_server_initial_conditions()
        self.server_world_generators = self.create_server_world_generators()
        self.server_decorators = self.create_server_decorators()
        self.server_quit_producers = self.create_server_quit_producers()

        # after create_server_world_generators(), because it will see python generated map
        # to pick a good location
        self.agent_start = []
        for self.current_agent in range(self.agent_count):
            self.agent_start.append(self.create_agent_start())

        # check that the observables (list) have no duplicate to_strings
        assert len([o.to_string() for o in self.observables]) == len(set([o.to_string() for o in self.observables]))
        assert len([a.to_string() for a in self.actionables]) == len(set([a.to_string() for a in self.actionables]))

        self._observation_space = self.create_observation_space()
        self._action_space = self.create_action_space()
        self._monitor_space = self.create_monitor_space()

    ########################
    ### API METHODS #######
    #######################

    ############## AGENT ##########################

    # observables
    @abstractmethod
    def create_observables(self) -> List[TranslationHandler]:
        """Specifies all of the observation handlers for the env specification.
        These are used to comprise the observation space.
        """
        raise NotImplementedError('subclasses must override create_observables()!')

    # actionables
    @abstractmethod
    def create_actionables(self) -> List[TranslationHandler]:
        """Specifies all of the action handlers for the env specification.
        These are used to comprise the action space.
        """
        raise NotImplementedError('subclasses must override create_actionables()!')

    # rewardables
    @abstractmethod
    def create_rewardables(self) -> List[TranslationHandler]:
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
        raise NotImplementedError('subclasses must override create_agent_start()!')

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

    @abstractmethod
    def create_monitors(self) -> List[TranslationHandler]:
        """Specifies all of the environment monitor handlers for the env specification.
        These are used to comprise the info dictionary returned by the environment.
        Note because of the way Gym1 works, these are not accessible at the first tick.

        These are also strictly typed (in terms of MineRLSpaces) just like observables and actionables.

        Any set of rewards/observables can go here.

        TODO (future): Allow monitors to accept state and action previously taken.
        """
        raise NotImplementedError('subclasses must override create_monitors()!')

    ##################### SERVER #########################

    @abstractmethod
    def create_server_initial_conditions(self) -> List[Handler]:
        raise NotImplementedError('subclasses must override create_server_initial_conditions()!')

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

    @property
    def monitor_space(self) -> Dict:
        return self._monitor_space

    def to_string(self):
        return self.name

    @abstractmethod
    def is_from_folder(self, folder: str) -> bool:
        raise NotImplementedError('subclasses must override is_from_folder()!')

    @abstractmethod
    def determine_success_from_rewards(self, rewards: list) -> bool:
        raise NotImplementedError('subclasses must override determine_success_from_rewards()')

    def _singlify(self, space: spaces.Dict):
        if self.is_single_agent:
            return space.spaces[self.agent_names[0]]
        else:
            return space

    def create_observation_space(self):
        return self._singlify(spaces.Dict({
            agent: spaces.Dict({
                o.to_string(): o.space for o in self.observables
            }) for agent in self.agent_names
        }))

    def create_action_space(self):
        return self._singlify(spaces.Dict({
            agent: spaces.Dict({
                a.to_string(): a.space for a in self.actionables
            }) for agent in self.agent_names
        }))

    def create_monitor_space(self):
        return self._singlify(spaces.Dict({
            agent: spaces.Dict({
                m.to_string(): m.space for m in self.monitors
            }) for agent in self.agent_names
        }))

    @abstractmethod
    def get_docstring(self):
        return NotImplemented

    def make(self, fake=False, **additonal_kwargs):
        """Turns the env_spec into a MineRLEnv

        Args:
            fake (bool, optional): Whether or not the env created should be fake.
            Defaults to False.
        """
        entry_point = self._entry_point(fake)
        module = importlib.import_module(entry_point.split(':')[0])
        class_ = getattr(module, entry_point.split(':')[-1])
        return class_(**self._env_kwargs(), **additonal_kwargs)

    def register(self, fake=False):
        reg_spec = dict(
            id=("Fake" if fake else "") + self.name,
            entry_point=self._entry_point(fake),
            kwargs=self._env_kwargs(),
            max_episode_steps=self.max_episode_steps,
        )
        if self.reward_threshold:
            reg_spec.update(dict(reward_threshold=self.reward_threshold))

        gym.register(**reg_spec)

    def _entry_point(self, fake: bool) -> str:
        if fake:
            return (
                EnvSpec.U_FAKE_SINGLE_AGENT_ENTRYPOINT if self.is_single_agent
                else EnvSpec.U_FAKE_MULTI_AGENT_ENTRYPOINT)
        else:
           return (
               EnvSpec.U_SINGLE_AGENT_ENTRYPOINT if self.is_single_agent
               else EnvSpec.U_MULTI_AGENT_ENTRYPOINT)

    def _env_kwargs(self) -> typing.Dict[str, typing.Any]:
        return {
            'env_spec': self,
        }

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

    def get_consolidated_xml(self, handlers: List[Handler]) -> List[str]:
        """Consolidates duplicate XML representations from the handlers.

        Deduplication happens by first getting all of the handler.xml() strings
        of the handlers, and then converting them into etrees. After that we check
        if there are any top level elements that are duplicated and pick the first of them
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
        trees = [etree.fromstring(xml) for xml in handler_xml_strs if xml != '']
        consolidated_trees = {tree.tag: tree for tree in trees}.values()

        return [etree.tostring(t, pretty_print=True).decode('utf-8')
                for t in consolidated_trees]

    def get_blacklist_reason(self, npz_data: dict) -> Optional[str]:
        """Return a non-empty str if `publish.py` should blacklist a demonstration.

        We can't catch all cases of bad demonstrations automatically, but overriding this
        method can allow for some quick, automatic filtering.

        Args:
            npz_data: A dict of numpy values from this demonstration about to be saved
            as "rendered.npz" by the publish.py stage of the dataset pipeline.

        Returns:
            Either None, or a nonempty str describing why this demonstration should be
            blacklisted.
        """
        if 'Survival' in self.name:
            return None

        # Various smoke-tests.
        ep_return = sum(npz_data['reward'])
        if ep_return == 1024.0 and 'Obtain' in self.name and 'SimonSays' not in self.name:
            return f"ep_return={ep_return} in non-SimonSays Obtain env was unexpectedly 1024"

        if ep_return < 64 and ('Obtain' not in self.name):
            return f"ep_return={ep_return} in non-Obtain env was unexpectedly low (<64)"

        if ep_return == 0.0:
            return "zero reward"

        if sum(npz_data['action$forward']) == 0:
            return "no forward movement"

        if sum(npz_data['action$attack']) == 0 and 'Navigate' not in self.name:
            return "no attack action on non-Navigate env"

        return None
