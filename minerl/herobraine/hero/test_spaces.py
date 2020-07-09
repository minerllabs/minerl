

#### TESTS


# Test that unmap composed with flat_map returns the original value
from minerl.herobraine.hero.spaces import Box, Dict, Discrete, MultiDiscrete, Enum
import collections
import numpy as np

def _test_batch_map(stackable_space, batch_dims = (32,16), no_op=False):
    n_in_batch = np.prod(batch_dims).astype(int)
    if no_op:
        batch = stackable_space.no_op(batch_dims)
    else:
        batch = np.array([stackable_space.sample() for _ in range(n_in_batch)])

        # Reshape into the batch dim
        batch =batch.reshape(list(batch_dims) + list(batch[0].shape))
    
    # Now map it through
    unmapped = stackable_space.unmap(stackable_space.flat_map(batch))
    if  unmapped.dtype.type is np.float:
        assert np.allclose(unmapped, batch)
    else:
        assert np.all(unmapped == batch)


# Test all of the spaces using _test_batch_map except for dict.
def test_batch_flat_map():
    for space in [
        Box(shape=[3, 2], low=-2, high=2, dtype=np.float32),
        Box(shape=[3], low=-2, high=2, dtype=np.float32),
        Box(shape=[], low=-2, high=2, dtype=np.float32),
        MultiDiscrete([3, 4]),
        MultiDiscrete([3]),
        Discrete(94),
        Enum('asd','sd','asdads','qweqwe')]:
        _test_batch_map(space)
        _test_batch_map(space, no_op=True)




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
def assert_equal_recursive(npa_dict, dict_to_test, atol=1.e-8):
    assert isinstance(npa_dict, collections.OrderedDict)
    assert isinstance(dict_to_test, collections.OrderedDict)
    for key, value in npa_dict.items():
        if isinstance(value, np.ndarray):
            if key == 'camera':
                assert np.allclose(value, dict_to_test[key], atol=1.5)
            elif value.dtype.type is np.string_ or value.dtype.type is np.str_:
                assert value == dict_to_test[key]
            else:
                assert np.allclose(value, dict_to_test[key], atol=atol)
            # assert np.array_equal(value, dict_to_test[key])
        elif isinstance(value, collections.OrderedDict):
            assert_equal_recursive(value, dict_to_test[key], atol)
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


