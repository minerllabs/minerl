from typing import Union

import gym
import numpy as np
import pytest

import minerl
from minerl.herobraine import envs
from minerl.herobraine.hero import spaces


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


def _replace_nested_gym_dicts_with_dicts(d: Union[dict, gym.spaces.Dict]) -> dict:
    result = {}
    if isinstance(d, gym.spaces.Dict):
        d = d.spaces
    for k, v in d.items():
        if isinstance(v, (dict, gym.spaces.Dict)):
            result[k] = _replace_nested_gym_dicts_with_dicts(v)
        else:
            result[k] = v
    return result


def _get_dummy_leaf_value_nested_dict(d: dict) -> dict:
    """Get a copy of the dict argument where every non-dict nested value (leaf value)
    is replaced by None.
    """
    # TODO(shwang): Maybe use something like type(leaf) instead of None to compare type
    #   of space.
    assert isinstance(d, dict)
    result = {}
    for k, v in d.items():
        if not isinstance(v, dict):
            result[k] = None
        else:
            result[k] = _get_dummy_leaf_value_nested_dict(v)
    return result


def _assert_matching_nested_keys(d1: dict, d2: dict) -> None:
    """Asserts that the keys of the two nested dicts are equal at all depths.

    More precisely, compares converts each dict argument into a copy of the dict where
    every non-dict nested value (leaf value) is replaced with None, and then asserts
    that the two transformed dicts are equal.

    In pytest, this provides a informational message about which keys are non-matching
    in the case of assertion failure.
    """
    dummy1 = _get_dummy_leaf_value_nested_dict(d1)
    dummy2 = _get_dummy_leaf_value_nested_dict(d2)
    assert dummy1 == dummy2


def _check_space(key, space, observation, correct_len):
    print('checking key {}'.format(key))
    if isinstance(space, spaces.Dict):
        for k, s in space.spaces.items():
            _check_space(k, s, observation[key], correct_len)
    else:
        allowed_spaces = (
            spaces.MultiDiscrete,
            spaces.Box,
            spaces.Discrete,
            spaces.Enum,
        )
        assert isinstance(space, allowed_spaces), "Unsupported dict type"
        print(f"checking key={key}, space=<{type(space).__name__}, shape={space.shape}>")


def _get_single_batch(env_name):
    d = minerl.data.make(env_name, num_workers=1)
    for batch in d.batch_iter(num_epochs=1, seq_len=2, batch_size=1):
        return batch


ENV_SPECS_BY_NAME = {env_spec.name: env_spec for env_spec in envs.HAS_DATASET_ENV_SPECS}

# We parametrize indirectly over `env_name` (and get inspect via ENV_SPECS_BY_NAME[env_name])
# rather directly parameterizing over `env_spec` because causes pytest to output failures
# that look like (A) rather than (B).
# (A) FAILED tests/data_ordering_test.py::test_first_batch_match_obs_keys[MineRLNavigate-v0]
# (B) FAILED tests/data_ordering_test.py::test_first_batch_match_obs_keys[env_spec6]
#
# Also, now we can select filter tests by name like
# `pytest test/data_ordering_test.py -k MineRLNavigate`
@pytest.mark.parametrize("env_name", ENV_SPECS_BY_NAME.keys())
# @pytest.mark.repeat(5)
class TestFirstBatches:
    @pytest.fixture
    def env_spec(self, env_name):
        return ENV_SPECS_BY_NAME[env_name]

    def test_first_batch_match_obs_keys(self, env_name, env_spec):
        obs = _get_single_batch(env_name)[0]
        _assert_matching_nested_keys(
            obs,
            _replace_nested_gym_dicts_with_dicts(env_spec.observation_space.spaces),
        )

    def test_first_batch_match_act_keys(self, env_name, env_spec):
        act = _get_single_batch(env_name)[1]
        _assert_matching_nested_keys(
            act,
            _replace_nested_gym_dicts_with_dicts(env_spec.action_space.spaces),
        )

    # def test_first_batch_space_shapes(self, env_spec):
    #     obs, act, rew, _, _ = _get_single_batch(env_spec.name)[0]
    #     correct_len = len(rew)
    #     for key, space in env_spec.observation_space.spaces.items():
    #         _check_space(key, space, obs, correct_len)
    #     for key, space in env_spec.action_space.spaces.items():
    #         _check_space(key, space, act, correct_len)
