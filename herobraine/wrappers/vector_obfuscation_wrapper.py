import collections
import numpy as np
from functools import reduce
from collections import OrderedDict

from typing import List

from gym import Space

from herobraine.env_spec import EnvSpec
from herobraine.hero import spaces
from herobraine.hero.spaces import Box
from herobraine.wrappers.util import union_spaces, flatten_spaces
from herobraine.wrappers.vector_wrapper import VecWrapper
from herobraine.wrappers.wrapper import EnvWrapper


def get_invertible_matrix_pair(shape):
    mat = np.random.random(shape)
    return mat, mat.T @ np.linalg.inv(mat @ mat.T)


class VectorObfWrapper(VecWrapper):
    def __init__(self, env_to_wrap: VecWrapper):
        super().__init__(env_to_wrap, name=env_to_wrap.name.split('-')[0] + 'Obf-' + env_to_wrap.name.split('-')[-1])
        self.obf_vector_len = 256

        # TODO load these from file
        np.random.seed(42)
        self.action_matrix, self.action_matrix_inverse = \
            get_invertible_matrix_pair([self.action_vector_len, self.obf_vector_len])
        self.observation_matrix, self.observation_matrix_inverse = \
            get_invertible_matrix_pair([self.observation_vector_len, self.obf_vector_len])

    def get_observation_space(self):
        obs_space = super().get_observation_space()
        obs_space.spaces['vector'] = spaces.Box(low=-np.inf, high=np.inf, shape=[self.obf_vector_len])
        return obs_space

    def get_action_space(self):
        act_space = super().get_action_space()
        act_space.spaces['vector'] = spaces.Box(low=-np.inf, high=np.inf, shape=[self.obf_vector_len])
        return act_space

    def wrap_observation(self, obs: OrderedDict) -> OrderedDict:
        obf_obs = super().wrap_observation(obs)
        obf_obs['vector'] = obf_obs['vector'].dot(self.observation_matrix)
        return obf_obs

    def wrap_action(self, act: OrderedDict) -> OrderedDict:
        wrapped_act = super().wrap_observation(act)
        wrapped_act['vector'] = wrapped_act['vector'].dot(self.action_matrix)
        return wrapped_act

    def unwrap_observation(self, wrapped_obs: OrderedDict) -> OrderedDict:
        wrapped_obs['vector'] = wrapped_obs['vector'].dot(self.observation_matrix_inverse)
        obs = super().unwrap_observation(wrapped_obs)
        return obs

    def unwrap_action(self, wrapped_act: OrderedDict) -> OrderedDict:
        wrapped_act['vector'] = wrapped_act['vector'].dot(self.action_matrix_inverse)
        act = super().unwrap_action(wrapped_act)
        return super().unwrap_action(act)

    def get_docstring(self):
        # TODO fix this
        return super().get_docstring()

