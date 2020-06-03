import numpy as np
from collections import OrderedDict

from minerl.herobraine.hero import spaces
from minerl.herobraine.wrappers.vector_wrapper import Vectorized
from minerl.herobraine.wrapper import EnvWrapper
import copy
import dill


def get_invertible_matrix_pair(shape):
    mat = np.random.random(shape)
    return mat, mat.T @ np.linalg.inv(mat @ mat.T)

OBG_VECTOR_LEN = 64
class Obfuscated(EnvWrapper):

    def __init__(self, env_to_wrap: Vectorized, obf_vector_len=64, name=''):
        self.obf_vector_len = obf_vector_len

        super().__init__(env_to_wrap)

        # TODO load these from file
        assert isinstance(env_to_wrap, Vectorized), 'Obfuscated env wrappers only supported for vectorized environments'

        # Get the directory for the actions
        with open('action.secret.compat', 'rb') as f:
            self.ac_enc, self.ac_dec = dill.load(f)

        with open('obs.secret.compat', 'rb') as f:
            self.obs_enc, self.obs_dec = dill.load(f)

        # Compute the no op vertors
        self.observation_no_op = self.env_to_wrap.wrap_observation(self.env_to_wrap.env_to_wrap.observation_space.no_op())['vector']
        self.action_no_op = self.env_to_wrap.wrap_action(self.env_to_wrap.env_to_wrap.action_space.no_op())['vector']

        if name:
            self.name = name

        

    def _update_name(self, name: str) -> str:
        return name.split('-')[0] + 'Obf-' + name.split('-')[-1]

    def create_observation_space(self):
        obs_space = copy.deepcopy(self.env_to_wrap.observation_space)
        # TODO: Properly compute the maximum
        obs_space.spaces['vector'] = spaces.Box(low=-1.05, high=1.05, shape=[self.obf_vector_len])
        return obs_space

    def create_action_space(self):
        act_space = copy.deepcopy(self.env_to_wrap.action_space)
        act_space.spaces['vector'] = spaces.Box(low=-1.05, high=1.05, shape=[self.obf_vector_len])
        return act_space

    def _wrap_observation(self, obs: OrderedDict) -> OrderedDict:
        obs['vector'] = self.obs_enc(obs['vector'])
        return obs

    def _wrap_action(self, act: OrderedDict) -> OrderedDict:
        act['vector'] = self.ac_enc(act['vector'])
        return act

    def _unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        obs['vector'] = np.clip(self.obs_dec(obs['vector']),0,1)
        return obs

    def _unwrap_action(self, act: OrderedDict) -> OrderedDict:
        act['vector'] = np.clip(self.ac_dec(act['vector']),0,1)
        return act

    def get_docstring(self):
        # TODO fix this
        return super().get_docstring()

