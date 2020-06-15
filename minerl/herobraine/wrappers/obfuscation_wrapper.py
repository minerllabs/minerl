from pathlib import Path
from typing import Union

import numpy as np
from collections import OrderedDict

from minerl.herobraine.hero import spaces
from minerl.herobraine.wrappers.vector_wrapper import Vectorized
from minerl.herobraine.wrapper import EnvWrapper
import copy
import os

# TODO: Force obfuscator nets to use these.
SIZE_FILE_NAME = 'size'
ACTION_OBFUSCATOR_FILE_NAME = 'act.secret.compat.npz'
OBSERVATION_OBFUSCATOR_FILE_NAME = 'obs.secret.compat.npz'


class Obfuscated(EnvWrapper):

    def __init__(self, env_to_wrap: Vectorized, obfuscator_dir, name=''):
        """The obfuscation class.

        Args:
            env_to_wrap (Vectorized): The vectorized environment to wrap.
            obfuscator_dir (str, os.path.Path): The path to the obfuscator neural networks.
            name (str, optional): A method to overide the name. Defaults to ''.
        """
        self.obf_vector_len, \
        self.ac_enc, self.ac_dec, \
        self.obs_enc, self.obs_dec = Obfuscated._get_obfuscator(obfuscator_dir)

        super().__init__(env_to_wrap)

        # TODO load these from file
        assert isinstance(env_to_wrap, Vectorized), 'Obfuscated env wrappers only supported for vectorized environments'

        # Compute the no op vertors
        self.observation_no_op = \
            self.env_to_wrap.wrap_observation(self.env_to_wrap.env_to_wrap.observation_space.no_op())['vector']
        self.action_no_op = self.env_to_wrap.wrap_action(self.env_to_wrap.env_to_wrap.action_space.no_op())['vector']

        if name:
            self.name = name

    @staticmethod
    def _get_obfuscator(obfuscator_dir: Union[str, Path]):
        """Gets the obfuscator from a directory.

        Args:
            obfuscator_dir (Union[str, Path]): The directory containg the pickled obfuscators.
        """

        def make_func(np_lays):
            def func(x):
                for t, data in np_lays:
                    if t == 'linear':
                        W, b = data
                        x = x.dot(W.T) + b
                    elif t == 'relu':
                        x = x * (x > 0)
                    elif t == 'subset_softmax':
                        discrete_subset = data
                        for (a, b) in discrete_subset:
                            y = x[..., a:b]
                            e_x = np.exp(y - np.max(x))
                            x[..., a:b] = e_x / e_x.sum(axis=-1)
                    else:
                        raise NotImplementedError()
                return x

            return func

        # TODO: This code should be centralized with the make_obfuscator network.

        assert os.path.exists(obfuscator_dir), "{} not found.".format(obfuscator_dir)
        assert set(os.listdir(obfuscator_dir)).issuperset(
            {OBSERVATION_OBFUSCATOR_FILE_NAME, ACTION_OBFUSCATOR_FILE_NAME, SIZE_FILE_NAME})

        # TODO: store size within the pdill.
        with open(os.path.join(obfuscator_dir, SIZE_FILE_NAME), 'r') as f:
            obf_vector_len = int(f.read())

        # Get the directory for the actions
        # ac_enc, ac_dec = np.load(f)
        ac_enc, ac_dec = np.load(os.path.join(obfuscator_dir, ACTION_OBFUSCATOR_FILE_NAME), allow_pickle=True)['arr_0']
        ac_enc, ac_dec = make_func(ac_enc), make_func(ac_dec)

        # obs_enc, obs_dec = dill.load(f)
        obs_enc, obs_dec = np.load(os.path.join(obfuscator_dir, OBSERVATION_OBFUSCATOR_FILE_NAME), allow_pickle=True)['arr_0']
        obs_enc, obs_dec = make_func(obs_enc), make_func(obs_dec)

        return obf_vector_len, ac_enc, ac_dec, obs_enc, obs_dec

    def _update_name(self, name: str) -> str:
        return name.split('-')[0] + 'Obf-' + name.split('-')[-1]

    def create_observation_space(self):
        obs_space = copy.deepcopy(self.env_to_wrap.observation_space)
        # TODO: Properly compute the maximum
        obs_space.spaces['vector'] = spaces.Box(low=-1.2, high=1.2, shape=[self.obf_vector_len])
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
        obs['vector'] = np.clip(
            self.obs_dec(obs['vector']),  # decode then CLIP
            0, 1)
        return obs

    def _unwrap_action(self, act: OrderedDict) -> OrderedDict:
        act['vector'] = np.clip(
            self.ac_dec(act['vector']),  # decode then CLIP
            0, 1)
        return act

    def get_docstring(self):
        # TODO fix this
        return super().get_docstring()
