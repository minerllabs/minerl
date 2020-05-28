import abc
from collections import OrderedDict

from herobraine.env_spec import EnvSpec


class EnvWrapper(EnvSpec):

    def __init__(self, env_to_wrap: EnvSpec):
        self.env_to_wrap = env_to_wrap
        super().__init__(self._update_name(env_to_wrap.name), env_to_wrap.xml, max_episode_steps=None, reward_threshold=None)

    @abc.abstractmethod
    def _update_name(self, name: str) -> str:
        pass

    @abc.abstractmethod
    def _wrap_observation(self, obs: OrderedDict) -> OrderedDict:
        pass

    def wrap_observation(self, obs: OrderedDict):
        # self = obfuscated
        # env_to_wrap = vector
        # obs is just a treechop ob
        if isinstance(self.env_to_wrap, EnvWrapper):
            obs = self.env_to_wrap.wrap_observation(obs)

        assert obs in self.env_to_wrap.get_observation_space()

        wrapped_obs =  self._wrap_observation(obs)

        assert wrapped_obs in self.get_observation_space()
        return wrapped_obs

    @abc.abstractmethod
    def _wrap_action(self, act: OrderedDict) -> OrderedDict:
        pass

    def wrap_action(self, act: OrderedDict):
        if isinstance(self.env_to_wrap, EnvWrapper):
            act = self.env_to_wrap.wrap_action(act)

        assert act in self.env_to_wrap.get_action_space()

        wrapped_act = self._wrap_action(act)
        
        assert wrapped_act in self.get_action_space()
        return wrapped_act

    @abc.abstractmethod
    def _unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        pass

    def unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        # self = obf
        # env_towrap = vect
        # obs = tofu_obs
        assert obs in self.get_observation_space()
        obs = self._unwrap_observation(obs)
        assert obs in self.env_to_wrap.get_observation_space()
        if isinstance(self.env_to_wrap, EnvWrapper):
            obs = self.env_to_wrap.unwrap_observation(obs)
        return obs

    @abc.abstractmethod
    def _unwrap_action(self, act: OrderedDict) -> OrderedDict:
        pass

    def unwrap_action(self, act: OrderedDict) -> OrderedDict:
        assert act in self.get_action_space()
        act = self._unwrap_action(act)
        assert act in self.env_to_wrap.get_action_space()
        # Todo: remove redundant assertion.

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
        return self.env_to_wrap.is_from_folder(folder)

    def create_mission_handlers(self):
        return self.env_to_wrap.create_mission_handlers()

    def create_actionables(self):
        return self.env_to_wrap.create_actionables()

    def create_observables(self):
        return self.env_to_wrap.create_observables()