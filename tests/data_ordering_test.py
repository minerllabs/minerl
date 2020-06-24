import time

import itertools
import gym
import sys
import tqdm
import numpy as np
import logging
import minerl.herobraine.hero.spaces as spaces

import minerl

logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig()

# TODO update these to include 2020 competition environments
ENVIRONMENTS = ['MineRLNavigate-v0',
                'MineRLNavigateDense-v0',
                'MineRLNavigateExtreme-v0',
                'MineRLNavigateExtremeDense-v0',
                'MineRLObtainIronPickaxe-v0',
                'MineRLObtainIronPickaxeDense-v0',
                'MineRLObtainDiamond-v0',
                'MineRLObtainDiamondDense-v0']


# Helper functions
def _check_shape(num_samples, sample_shape, obs):
    if isinstance(obs, list):
        assert (len(obs)) == num_samples
    elif isinstance(obs, np.ndarray):
        assert (obs.shape[0] == num_samples)
        for i in range(len(obs.shape) - 2):
            assert (obs.shape[i + 2] == sample_shape[i])
    else:
        assert False, "unsupported data type"


def _check_space(key, space, observation, correct_len):
    logging.debug('checking key {}'.format(key))
    if isinstance(space, spaces.Dict):
        for k, s in space.spaces.items():
            _check_space(k, s, observation[key], correct_len)
    elif isinstance(space, spaces.MultiDiscrete):
        # print("MultiDiscrete")
        # print(space.shape)
        # print(observation[key])
        _check_shape(correct_len, space.shape, observation[key])
    elif isinstance(space, spaces.Box):
        # print("Box")
        # print(space.shape)
        # print(observation[key])
        _check_shape(correct_len, space.shape, observation[key])
    elif isinstance(space, spaces.Discrete):
        # print("Discrete")
        # print(space.shape)
        # print(observation[key])
        _check_shape(correct_len, space.shape, observation[key])
    elif isinstance(space, spaces.Enum):
        # print("Enum")
        # print(space.shape)
        # print(observation[key])
        _check_shape(correct_len, space.shape, observation[key])
    else:
        assert False, "Unsupported dict type"


def _test_data(environment='MineRLObtainDiamond-v0'):
    for _ in range(20):
        run_once(environment, verbose=False)
    return True


def run_once(environment, verbose=True):
    d = minerl.data.make(environment, num_workers=1)
    if verbose:
        logging.info('Testing {}'.format(environment))

    # Iterate through single batch of data
    for obs, act, rew, nObs, done in d.batch_iter(num_epochs=1, seq_len=2, batch_size=1):
        correct_len = len(rew)
        for key, space in d.observation_space.spaces.items():
            _check_space(key, space, obs, correct_len)

        for key, space in d.action_space.spaces.items():
            _check_space(key, space, act, correct_len)

        break
    return True


def _test_navigate():
    run_once('MineRLNavigate-v0')
    run_once('MineRLNavigateDense-v0')


def _test_navigate_extreme():
    run_once('MineRLNavigateExtreme-v0')
    run_once('MineRLNavigateExtremeDense-v0')


def _test_obtain_iron_pickaxe():
    run_once('MineRLObtainIronPickaxe-v0')
    run_once('MineRLObtainIronPickaxeDense-v0')


def _test_obtain_diamond():
    run_once('MineRLObtainDiamond-v0')
    run_once('MineRLObtainDiamondDense-v0')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        rate = _test_data(sys.argv[1])
    else:
        rate = _test_data()
