

#### TESTS


# Test that unmap composed with flat_map returns the original value
from herobraine.hero.spaces import Box, Dict, Discrete, MultiDiscrete, Enum
import collections
import numpy as np

def test_unmap_flat_map():
    md = MultiDiscrete([3, 4])
    x = md.sample()
    assert (np.array_equal(md.unmap(md.flat_map(x)), x))

    # Test that unmap composed with flat_map returns the original value


def test_box_flat_map():
    b = Box(shape=[3, 2], low=-2, high=2, dtype=np.float32)
    x = b.sample()
    assert (np.allclose(b.unmap(b.flat_map(x)), x))


# A method which asserts equality between an ordered dict of numpy arrays and another
# ordered dict - WTH
def assert_equal_recursive(npa_dict, dict_to_test):
    assert isinstance(npa_dict, collections.OrderedDict)
    assert isinstance(dict_to_test, collections.OrderedDict)
    for key, value in npa_dict.items():
        if isinstance(value, np.ndarray):
            assert np.allclose(value, dict_to_test[key])
            # assert np.array_equal(value, dict_to_test[key])
        elif isinstance(value, collections.OrderedDict):
            assert_equal_recursive(value, dict_to_test[key])
        else:
            assert value == dict_to_test[key]


# Test that unmap composed with flat_map returns the original value
def test_unmap_flat_map_dict():
    d = Dict({'a': Box(
        shape=[3, 2], low=-2, high=2,
        dtype=np.float32
    )})
    x = d.sample()
    assert_equal_recursive(d.unmap(d.flat_map(x)), x)


# Test that unmap composed with flat_map returns the original value
def test_unmap_flat_map_discrete():
    d = Discrete(5)
    x = d.sample()
    assert (np.array_equal(d.unmap(d.flat_map(x)), x))

    # Test that unmap composed with flat_map returns the original value


def test_unmap_flat_map_enum():
    d = Enum('type1', 'type2')
    x = d.sample()
    assert (np.array_equal(d.unmap(d.flat_map(x)), x))


def test_all():
    d = Dict({
        'one': MultiDiscrete([3, 4]),
        'two': Box(low=0, high=1, shape=[6]),
        'three': Discrete(5),
        'four': Enum('type1', 'type2'),
        'five': Enum('type1'),
        'six': Dict({'a': Box(
            shape=[3, 2], low=-1, high=2,
            dtype=np.float32)
        })
    })

    x = d.sample()
    assert_equal_recursive(d.unmap(d.flat_map(x)), x)


# Tests unmap composed with flat_map on all of the MineRLSpaces
# this will test all numpy-only spaces
def test_all_flat_map_numpy_only():
    spaces = [
        Box(low=-10, high=10, shape=(5,), dtype=np.int64),
        Discrete(10),
        Discrete(100),
        Discrete(1000),
        Enum('a', 'b', 'c')
    ]
    for space in spaces:
        x = space.sample()
        x_flat = space.flat_map(x)
        assert np.array_equal(x, space.unmap(x_flat))


# Tests unmap composed with flat_map on all of the MineRLSpaces
# this test uses a very nested dict space to
def test_all_flat_map_nested_dict():
    all_spaces = Dict({
        'a': Dict({
            'b': Dict({
                'c': Discrete(10)
            }),
            'd': Discrete(10)
        }),
        'e': Dict({
            'f': Discrete(10)
        })
    })
    x = all_spaces.sample()
    assert_equal_recursive(all_spaces.unmap(all_spaces.flat_map(x)), x)


