import abc
from collections import OrderedDict

import gym

from herobraine.env_spec import EnvSpec


class EnvWrapper(EnvSpec):

    @abc.abstractmethod
    def wrap_observation(self, obs: OrderedDict) -> OrderedDict:
        pass

    @abc.abstractmethod
    def wrap_action(self, act: OrderedDict) -> OrderedDict:
        pass

    @abc.abstractmethod
    def unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        pass

    @abc.abstractmethod
    def unwrap_action(self, act: OrderedDict) -> OrderedDict:
        pass

    @abc.abstractmethod
    def get_observation_space(self):
        pass

    @abc.abstractmethod
    def get_action_space(self):
        pass

    @abc.abstractmethod
    def get_docstring(self):
        pass
