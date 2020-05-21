

### TESTS ###

# A method which asserts equality between an ordered dict of numpy arrays and another
# ordered dict - WTH
import collections
from herobraine.wrappers import vector_wrapper
import herobraine.env_specs as envs
from herobraine.wrappers.util import union_spaces
import numpy as np


def assert_equal_recursive(npa_dict, dict_to_test):
    assert isinstance(npa_dict, collections.OrderedDict)
    assert isinstance(dict_to_test, collections.OrderedDict)
    for key, value in npa_dict.items():
        if isinstance(value, np.ndarray):
            assert np.array_equal(value, dict_to_test[key])
        elif isinstance(value, collections.OrderedDict):
            assert_equal_recursive(value, dict_to_test[key])
        else:
            assert value == dict_to_test[key]

def test_wrap_unwrap_action():
    """
    Tests that wrap_action composed with unwrap action is the identity.
    1. Construct an VecWrapper of an EnvSpec called ObtainDiamond
    2. Sample actions from its action space
    3. Wrap and unwrap those actions.
    4. Assert that the result is the same as the sample
    """
    base_env = envs.MINERL_OBTAIN_DIAMOND_V0
    print(base_env)
    vec_env = vector_wrapper.VecWrapper(base_env)

    s = base_env.get_action_space().sample()
    ws = vec_env.wrap_action(s)
    us = vec_env.unwrap_action(ws)
    assert_equal_recursive(s, us)

def test_wrap_unwrap_observation():
    """
    Tests that wrap_observation composed with unwrap observation is the identity.
    1. Construct an VecWrapper of an EnvSpec called ObtainDiamond
    2. Sample observation from its observation space
    3. Wrap and unwrap those observations.
    4. Assert that the result is the same as the sample
    """
    base_env = envs.MINERL_OBTAIN_DIAMOND_V0
    print(base_env)
    vec_env = vector_wrapper.VecWrapper(base_env)

    s = base_env.get_observation_space().sample()
    ws = vec_env.wrap_observation(s)
    us = vec_env.unwrap_observation(ws)
    assert_equal_recursive(s, us)

# test_wrap_unwrap()


def test_union_spaces():
    env_1 = envs.MINERL_TREECHOP_V0.actionables
    env_2 = envs.MINERL_NAVIGATE_DENSE_V0.actionables
    print(union_spaces(env_2, env_1))