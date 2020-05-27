import numpy as np
from collections import OrderedDict

from herobraine.hero import spaces
from herobraine.wrappers.vector_wrapper import Vectorized
from herobraine.wrappers.wrapper import EnvWrapper


def get_invertible_matrix_pair(shape):
    mat = np.random.random(shape)
    return mat, mat.T @ np.linalg.inv(mat @ mat.T)


class Obfuscated(EnvWrapper):

    def __init__(self, env_to_wrap: Vectorized):
        super().__init__(env_to_wrap)

        self.obf_vector_len = 49

        # TODO load these from file
        assert isinstance(env_to_wrap, Vectorized), 'Obfuscated env wrappers only supported for vectorized environments'
        np.random.seed(42)
        self.action_matrix, self.action_matrix_inverse = \
            get_invertible_matrix_pair([self.env_to_wrap.action_vector_len, self.obf_vector_len])
        self.observation_matrix, self.observation_matrix_inverse = \
            get_invertible_matrix_pair([self.env_to_wrap.observation_vector_len, self.obf_vector_len])

    def _update_name(self, name: str) -> str:
        return name.split('-')[0] + 'Obf-' + name.split('-')[-1]

    def get_observation_space(self):
        obs_space = super().get_observation_space()
        obs_space.spaces['vector'] = spaces.Box(low=-np.inf, high=np.inf, shape=[self.obf_vector_len])
        return obs_space

    def get_action_space(self):
        act_space = self.env_to_wrap.get_action_space()
        act_space.spaces['vector'] = spaces.Box(low=-np.inf, high=np.inf, shape=[self.obf_vector_len])
        return act_space

    def _wrap_observation(self, obs: OrderedDict) -> OrderedDict:
        obs['vector'] = obs['vector'] @ (self.observation_matrix)
        return obs

    def _wrap_action(self, act: OrderedDict) -> OrderedDict:
        act['vector'] = act['vector'] @ (self.action_matrix)
        return act

    def _unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        obs['vector'] = obs['vector'] @ (self.observation_matrix_inverse)
        return obs

    def _unwrap_action(self, act: OrderedDict) -> OrderedDict:
        act['vector'] = act['vector'] @ (self.action_matrix_inverse)
        return act

    def get_docstring(self):
        # TODO fix this
        return super().get_docstring()

