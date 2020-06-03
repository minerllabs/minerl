import numpy as np
from collections import OrderedDict

from minerl.herobraine.hero import spaces
from minerl.herobraine.wrappers.vector_wrapper import Vectorized
from minerl.herobraine.wrappers.wrapper import EnvWrapper
import copy

import dill


class ObfuscatedNet(EnvWrapper):

    def __init__(self, env_to_wrap: Vectorized, obf_vector_len=256, name=''):
        self.obf_vector_len = obf_vector_len

        super().__init__(env_to_wrap)

        assert isinstance(env_to_wrap, Vectorized), 'Obfuscated Neural Network wrappers only support vectorized environments'

        self.encode_action = NN('weights.npz').encode
        self.encode_observation = NN('weights.npz').encode
        self.decode_action = NN('weights.npz').decode
        self.decode_observation = NN('weights.npz').decode

        # Compute the no op vertors
        self.observation_no_op = self.wrap_observation(self.env_to_wrap.env_to_wrap.observation_space.no_op())['vector']
        self.action_no_op = self.wrap_action(self.env_to_wrap.env_to_wrap.action_space.no_op())['vector']

        if name:
            self.name = name

        

    def _update_name(self, name: str) -> str:
        return name.split('-')[0] + 'Obf-' + name.split('-')[-1]

    def create_observation_space(self):
        obs_space = copy.deepcopy(self.env_to_wrap.observation_space)
        obs_space.spaces['vector'] = spaces.Box(low=-1, high=1, shape=[self.obf_vector_len])
        return obs_space

    def create_action_space(self):
        act_space = copy.deepcopy(self.env_to_wrap.action_space)
        act_space.spaces['vector'] = spaces.Box(low=-1, high=1, shape=[self.obf_vector_len])
        return act_space

    def _wrap_observation(self, obs: OrderedDict) -> OrderedDict:
        obs['vector'] = self.encode_observation(obs['vector'])
        return obs

    def _wrap_action(self, act: OrderedDict) -> OrderedDict:
        act['vector'] = self.encode_action(act['vector'])
        return act

    def _unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        obs['vector'] = self.decode_observation(obs['vector'])
        return obs

    def _unwrap_action(self, act: OrderedDict) -> OrderedDict:
        obs['vector'] = self.decode_action(obs['vector'])
        return act

    def get_docstring(self):
        # TODO fix this
        return super().get_docstring()

