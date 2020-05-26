import collections
import numpy as np
from functools import reduce
from collections import OrderedDict

from typing import List

from herobraine.env_spec import EnvSpec
from herobraine.hero import spaces
from herobraine.hero.spaces import Box
from herobraine.wrappers.util import union_spaces, flatten_spaces
from herobraine.wrappers.wrapper import EnvWrapper


class VecWrapper(EnvWrapper):
    def create_mission_handlers(self):
        pass

    def create_observables(self):
        return self.common_observations

    def create_actionables(self):
        return self.common_actions

    @staticmethod
    def is_from_folder(folder: str) -> bool:
        pass

    def __init__(self, env_to_wrap: EnvSpec, common_env=None, name=None):
        self.env_to_wrap = env_to_wrap
        self.common_env = env_to_wrap if common_env is None else common_env        

        # Gather all of the handlers for the common_env
        self.common_actions = union_spaces(self.env_to_wrap.actionables, self.common_env.actionables)
        self.common_observations = union_spaces(self.env_to_wrap.observables, self.common_env.observables)
        self.flat_actions, self.remaining_action_space = flatten_spaces(self.common_actions)
        self.flat_observations, self.remaining_observation_space = flatten_spaces(self.common_observations)
        self.action_vector_len = sum(space.shape[0] for space in self.flat_actions)
        self.observation_vector_len = sum(space.shape[0] for space in self.flat_observations)

        self.env_name = name if name is not None else env_to_wrap.name
        super().__init__(self.env_name.split('-')[0] + 'Vector-' + self.env_name.split('-')[-1],
                         env_to_wrap.xml)

    def wrap_observation(self, obs: OrderedDict) -> OrderedDict:
        flat_obs_part = self.common_env.get_observation_space().flat_map(obs)
        wrapped_obs = self.common_env.get_observation_space().unflattenable_map(obs)
        wrapped_obs['vector'] = flat_obs_part
        return wrapped_obs

    def wrap_action(self, act: OrderedDict) -> OrderedDict:
        flat_act_part = self.common_env.get_action_space().flat_map(act)
        wrapped_act = self.common_env.get_action_space().unflattenable_map(act)
        wrapped_act['vector'] = flat_act_part
        return wrapped_act

    def unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        return self.common_env.get_observation_space().unmap_mixed(obs['vector'], obs)

    def unwrap_action(self, act: OrderedDict) -> OrderedDict:
        return self.common_env.get_action_space().unmap_mixed(act['vector'], act)

    def get_observation_space(self):
        obs_list = self.remaining_observation_space
        obs_list.append(('vector',  spaces.Box(low=0, high=1, shape=[self.observation_vector_len], dtype=np.float32)))
        return spaces.Dict(spaces=OrderedDict(obs_list))

    def get_flattenable_observation_space(self):
        # TODO use this merged space to wrap actions
        obs_list = [(hdl.to_string(), hdl.space) for hdl in self.common_observations]
        return spaces.Dict(spaces=OrderedDict(obs_list))

    def get_action_space(self):
        act_list = self.remaining_action_space
        act_list.append(('vector', spaces.Box(low=0, high=1, shape=[self.action_vector_len], dtype=np.float32)))
        return spaces.Dict(spaces=OrderedDict(act_list))

    def get_flattenable_action_space(self):
        act_list = [(hdl.to_string(), hdl.space) for hdl in self.common_actions]
        return spaces.Dict(spaces=OrderedDict(act_list))

    def get_docstring(self):
        return self.env_to_wrap.get_docstring()
