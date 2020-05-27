import numpy as np
from functools import reduce
from collections import OrderedDict

from herobraine.env_spec import EnvSpec
from herobraine.hero import spaces
from herobraine.wrappers.util import union_spaces, flatten_spaces
from herobraine.wrappers.wrapper import EnvWrapper


class Vectorized(EnvWrapper):
    """
    Normalizes and flattens a typical env space for obfuscation.
    """
    def _update_name(self, name: str) -> str:
        return name.split('-')[0] + 'Vector-' + name.split('-')[-1]

    @staticmethod
    def is_from_folder(folder: str) -> bool:
        pass

    def __init__(self, env_to_wrap: EnvSpec, common_envs=None):
        self.env_to_wrap = env_to_wrap
        self.common_envs = [env_to_wrap] if common_envs is None or len(common_envs) == 0 else common_envs

        # Gather all of the handlers for the common_env
        self.common_actions = reduce(union_spaces, [env.actionables for env in self.common_envs])
        self.common_action_space = spaces.Dict(
            [(hdl.to_string(), hdl.space) for hdl in self.common_actions])
        self.common_observations = reduce(union_spaces, [env.observables for env in self.common_envs])
        self.common_observation_space = spaces.Dict(
            [(hdl.to_string(), hdl.space) for hdl in self.common_observations])
        self.flat_actions, self.remaining_action_space = flatten_spaces(self.common_actions)
        self.flat_observations, self.remaining_observation_space = flatten_spaces(self.common_observations)

        self.action_vector_len = sum(space.shape[0] for space in self.flat_actions)
        self.observation_vector_len = sum(space.shape[0] for space in self.flat_observations)

        super().__init__(env_to_wrap)

    def create_observables(self):
        return self.common_observations

    def create_actionables(self):
        return self.common_actions

    def _wrap_observation(self, obs: OrderedDict) -> OrderedDict:
        flat_obs_part = self.common_observation_space.flat_map(obs)
        wrapped_obs = self.common_observation_space.unflattenable_map(obs)
        wrapped_obs['vector'] = flat_obs_part
        return wrapped_obs

    def _wrap_action(self, act: OrderedDict) -> OrderedDict:
        flat_act_part = self.common_action_space.flat_map(act)
        wrapped_act = self.common_action_space.unflattenable_map(act)
        wrapped_act['vector'] = flat_act_part
        return wrapped_act

    def _unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        return self.common_observation_space.unmap_mixed(obs['vector'], obs)

    def _unwrap_action(self, act: OrderedDict) -> OrderedDict:
        return self.common_action_space.unmap_mixed(act['vector'], act)

    def get_observation_space(self):
        obs_list = self.remaining_observation_space
        obs_list.append(('vector', spaces.Box(low=0, high=1, shape=[self.observation_vector_len], dtype=np.float32)))
        return spaces.Dict(OrderedDict(obs_list))

    def get_action_space(self):
        act_list = self.remaining_action_space
        act_list.append(('vector', spaces.Box(low=0, high=1, shape=[self.action_vector_len], dtype=np.float32)))
        return spaces.Dict(OrderedDict(act_list))

    def get_docstring(self):
        return self.env_to_wrap.get_docstring()
