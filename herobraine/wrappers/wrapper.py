import abc
from collections import OrderedDict

import gym

from herobraine.env_spec import EnvSpec


class EnvWrapper(EnvSpec):

    def __init__(self, env_to_wrap: EnvSpec):
        self.env_to_wrap = env_to_wrap
        super().__init__(self.update_name(env_to_wrap.name), env_to_wrap.xml, max_episode_steps=None, reward_threshold=None)

    @abc.abstractmethod
    def _update_name(self, name: str) -> str:
        pass

    def update_name(self, name: str) -> str:
        if isinstance(self.env_to_wrap, EnvWrapper):
            name = self.env_to_wrap.update_name(name)
        return self._update_name(name)

    @abc.abstractmethod
    def _wrap_observation(self, obs: OrderedDict) -> OrderedDict:
        pass

    def wrap_observation(self, obs: OrderedDict):
        if isinstance(self.env_to_wrap, EnvWrapper):
            obs = self.env_to_wrap.wrap_observation(obs)
        return self._wrap_observation(obs)

    @abc.abstractmethod
    def _wrap_action(self, act: OrderedDict) -> OrderedDict:
        pass

    def wrap_action(self, act: OrderedDict):
        if isinstance(self.env_to_wrap, EnvWrapper):
            act = self.env_to_wrap.wrap_action(act)
        return self._wrap_action(act)

    @abc.abstractmethod
    def _unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        pass

    def unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        obs = self._unwrap_observation(obs)
        if isinstance(self.env_to_wrap, EnvWrapper):
            obs = self.env_to_wrap.unwrap_observation(obs)
        return obs

    @abc.abstractmethod
    def _unwrap_action(self, act: OrderedDict) -> OrderedDict:
        pass

    def unwrap_action(self, act: OrderedDict) -> OrderedDict:
        act = self._unwrap_action(act)
        if isinstance(self.env_to_wrap, EnvWrapper):
            act = self.env_to_wrap.unwrap_action(act)
        return act

    def get_observation_space(self):
        return self.env_to_wrap.get_observation_space()

    def get_action_space(self):
        return self.env_to_wrap.get_action_space()

    def get_docstring(self):
        return self.env_to_wrap.get_docstring()
        
    def is_from_folder(self, folder: str) -> bool:
        return self.env_to_wrap.is_from_folder()

    def create_mission_handlers(self):
        return self.env_to_wrap.create_mission_handlers()

    def create_actionables(self):
        return self.env_to_wrap.create_actionables()

    def create_observables(self):
        return self.env_to_wrap.create_observables()