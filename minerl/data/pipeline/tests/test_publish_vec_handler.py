import numpy as np
import json
import signal
import tarfile

import pytest

import minerl.herobraine.env_specs as envs

import gym

from minerl.data.util.constants import DATA_DIR


@pytest.mark.skip
def test_render_data():
    # Obfuscated Treechop Environment Spec
    env = 'MineRLTreechopVector-v0'

    environment = envs.create_spec(gym.envs.registration.spec(env), folder=None, name=env)
    handler_dict = np.load('pipeline/tests_data/treechop.npz')

    action_keys = [(key, key[7:]) for key in handler_dict.keys() if key.startswith('action_')]
    observation_keys = [(key, key[12:]) for key in handler_dict.keys() if key.startswith('observation_')]

    action_dict = {handler_str: handler_dict[key] for key, handler_str in action_keys}
    observation_dict = {handler_str: handler_dict[key] for key, handler_str in observation_keys}

    published = dict()
    num_ticks = len(handler_dict['reward'])

    published['action'] = np.stack(
        [environment['action_wrapper']({key: arr[tick] for key, arr in action_dict.items()})
         for tick in range(num_ticks)]
    )

    published['observation'] = np.stack(
        [environment['observation_wrapper']({key: arr[tick] for key, arr in observation_dict.items()})
         for tick in range(num_ticks)]
    )
