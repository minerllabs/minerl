import random
from collections import OrderedDict
from typing import List

import gym
import gym.spaces
import numpy as np
import collections

import abc

import string


class MineRLSpace(abc.ABC):

    @property
    def flattened(self) -> gym.spaces.Box:
        if not hasattr(self,"_flattened") :
            self._flattened = self.create_flattened_space()
        return self._flattened
        
    @abc.abstractmethod
    def no_op(self):
        pass

    @abc.abstractmethod
    def create_flattened_space(self) -> gym.spaces.Box:
        pass
    
    @abc.abstractmethod
    def flat_map(self, x):
        pass

    @abc.abstractmethod
    def unmap(self, x):
        pass
        

class Box(gym.spaces.Box, MineRLSpace):
    def no_op(self):
        return np.zeros(shape=self.shape).astype(self.dtype)

    def create_flattened_space(self):
        if len(self.shape) > 2:
            return self
        else:
            return Box(low=self.low.flatten(), high=(self.high.flatten()) )
            
    def flat_map(self, x):
        return x.flatten()

    def unmap(self, x):
        return x.reshape(self.shape)


class Discrete(gym.spaces.Discrete, MineRLSpace):
    def __init__(self, *args, **kwargs):
        super(Discrete, self).__init__(*args, **kwargs)
        self.eye = np.eye(self.n)
        
    def no_op(self):
        return 0

    def create_flattened_space(self):
        return Box(low=0, high=1, shape=(self.n,))

    def flat_map(self, x):
        return self.eye[x]

    def unmap(self, x):
        return np.argmax(x).flatten().tolist()[0]



class Enum(Discrete, MineRLSpace):
    """
    An enum space. It can either be the enum string or a integer.
    """

    def __init__(self, *values: str):
        """Initializes the Enum space with a set of possible
        values that the enum can take.

        Usage:
        ```
        x = Enum('none', 'type1', 'type2')
        x['none'] # 0
        x['type1'] # 1

        Args:
            values (str):  An order argument list of values the enum can take.
        """
        if not isinstance(values,tuple):
            values = (values,)
        super().__init__(len(values))
        self.values = values

    def sample(self) -> int:
        """Samples a random index for one of the enum types.

        ```
        x.sample() # A random nubmer in the half-open discrete interval [0, len(x.values))
        ````

        Returns:
            int:  A random index for one of the enum types.
        """
        return super().sample()
    

    def __getitem__(self, action):
        try:
            if isinstance(action, str):
                return self.values.index(action)
            elif action < self.n:
                return action
        except ValueError:
            raise ValueError("\"{}\" not valid ENUM value in values {}".format(action, self.values))
        finally:
            # TODO support more action formats through np.all < super().n
            raise ValueError("minerl.spaces.Enum: action must be of type str or int")

    def __str__(self):
        return "Enum(" + ','.join(self.values) + ")"

    def __len__(self):
        return len(self.values)


class Dict(gym.spaces.Dict, MineRLSpace):

    def no_op(self):
        return OrderedDict([(k, space.no_op()) for k, space in self.spaces.items()])

    def create_flattened_space(self):
        shape = sum([s.flattened.shape[0] for s in self.spaces.values()])
        return Box(low=0, high=1, shape=[shape], dtype=np.float32)

    def flat_map(self, x):
        return np.concatenate(
           [v.flat_map(x[k]) for k,v in (self.spaces.items())]
        )
    
    def unmap(self, x):
        # split x
        unmapped = collections.OrderedDict()
        cur_index = 0
        for k,v in self.spaces.items():
            unmapped[k] = v.unmap(x[cur_index:cur_index+v.flattened.shape[0]])
            cur_index += v.flattened.shape[0]
        
        return unmapped


class MultiDiscrete(gym.spaces.MultiDiscrete, MineRLSpace):
    def __init__(self, *args, **kwargs):
        super(MultiDiscrete, self).__init__(*args, **kwargs)
        self.eyes = [np.eye(n) for n in self.nvec]

    def no_op(self):
        return (np.zeros(self.nvec.shape) * self.nvec).astype(self.dtype)

    def create_flattened_space(self):
        return Box(low=0, high=1, shape=[
            np.sum(self.nvec)
        ])

    def flat_map(self,x):
        return np.concatenate(
            [self.eyes[i][x[i]] for i in range(len(self.nvec))]
        )
        
    def unmap(self, x):
        cur_index = 0
        out = []
        for n in self.nvec:
            out.append(np.argmax(x[cur_index:cur_index + n]).flatten())
            cur_index += n
        return np.concatenate(out)


class Text(gym.Space, MineRLSpace):
    """
    [['a text string', ..., 'last_text_string']]

    Example usage:
    self.observation_space = spaces.Text(1)
    """
    MAX_STR_LEN = 100

    def __init__(self, shape):
        super().__init__(shape, np.unicode_)

    def sample(self):
        total_strings = np.prod(self.shape)
        strings = [
            "".join([random.choice(string.ascii_uppercase) for _ in range(random.randint(0, Text.MAX_STR_LEN))])
            for _ in range(total_strings)
        ]
        return np.array(np.reshape(strings, self.shape), np.dtype)

    def contains(self, x):
        contained = False
        contained = contained or isinstance(x, np.ndarray) and x.shape == self.shape and x.dtype in [np.string,
                                                                                                     np.unicode]
        contained = contained or self.shape in [None, 1] and isinstance(x, str)
        return contained

    __contains__ = contains

    def to_jsonable(self, sample_n):
        return np.array(sample_n, dtype=self.dtype).to_list()

    def from_jsonable(self, sample_n):
        return [np.asarray(sample, dtype=self.dtype) for sample in sample_n]

    def __repr__(self):
        return "Text" + str(self.shape)


class List(gym.Space, MineRLSpace):
    """
    A list (i.e., product) of simpler spaces

    Example usage:
    self.observation_space = spaces.List((spaces.Discrete(2), spaces.Discrete(3)))
    """

    def __init__(self, spaces):
        self.spaces = spaces
        gym.Space.__init__(self, None, None)

    def sample(self):
        return list([space.sample() for space in self.spaces])

    def contains(self, x):
        if isinstance(x, list):
            x = list(x)  # Promote list to tuple for contains check
        return isinstance(x, list) and len(x) == len(self.spaces) and all(
            space.contains(part) for (space, part) in zip(self.spaces, x))

    def __repr__(self):
        return "List(" + ", ".join([str(s) for s in self.spaces]) + ")"


    def to_jsonable(self, sample_n):
        # serialize as list-repr of tuple of vectors
        return [space.to_jsonable([sample[i] for sample in sample_n]) \
                for i, space in enumerate(self.spaces)]

    def from_jsonable(self, sample_n):
        return [sample for sample in zip(*[space.from_jsonable(sample_n[i]) for i, space in enumerate(self.spaces)])]


class DiscreteRange(Discrete, MineRLSpace):
    """
    {begin, begin+1, ..., end-2, end - 1}
    
    Like discrete, but takes a range of dudes
    DiscreteRange(0, n) is equivalent to Discrete(n)

    Examples usage:
    self.observation_space = spaces.DiscreteRange(-1, 3)
    """

    def __init__(self, begin, end):
        self.begin = begin
        self.end = end
        super().__init__(end-begin)

    def sample(self):
        return super().sample() + self.begin

    def contains(self, x):
        return super().contains(x - self.begin)

    def __repr__(self):
        return "DiscreteRange({}, {})".format(self.begin, self.n + self.begin)

    def __eq__(self, other):
        return self.n == other.n and self.begin == other.begin




#### TESTS


# Test that unmap composed with flat_map returns the original value
def test_unmap_flat_map():
    md = MultiDiscrete([3,4])
    x = md.sample()
    assert(np.array_equal(md.unmap(md.flat_map(x)), x))

    # Test that unmap composed with flat_map returns the original value
def test_box_flat_map():
    b = Box(shape=[3,2], low=-2, high=2, dtype=np.float32)
    x = b.sample()
    assert(np.array_equal(b.unmap(b.flat_map(x)), x))


# A method which asserts equality between an ordered dict of numpy arrays and another
# ordered dict - WTH
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
            
# Test that unmap composed with flat_map returns the original value
def test_unmap_flat_map_dict():
    d = Dict({'a': Box(
        shape=[3,2], low=-2, high=2,
        dtype=np.float32
    )})
    x = d.sample()
    assert_equal_recursive(d.unmap(d.flat_map(x)), x)

# Test that unmap composed with flat_map returns the original value
def test_unmap_flat_map_discrete():
    d = Discrete(5)
    x = d.sample()
    assert(np.array_equal(d.unmap(d.flat_map(x)), x))

    # Test that unmap composed with flat_map returns the original value
def test_unmap_flat_map_enum():
    d = Enum(['type1', 'type2'])
    x = d.sample()
    assert(np.array_equal(d.unmap(d.flat_map(x)), x))


def test_all():
    d = Dict({
        'one': MultiDiscrete([3,4]),
        'two': Box(low=0, high=1, shape=[6]),
        'three': Discrete(5),
        'four': Enum('type1', 'type2'),
        'five': Enum('type1'),
        'six': Dict({'a': Box(
            shape=[3,2], low=-1, high=2,
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
        Enum('a','b','c')
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
    assert_equal_recursive(all_spaces.flat_map(x).unmap(all_spaces), x)


if __name__ == "__main__":
    test_unmap_flat_map()
    test_unmap_flat_map_dict()
    test_unmap_flat_map_discrete()
    test_unmap_flat_map_enum()
    test_all()
    test_all_flat_map_numpy_only()
    test_all_flat_map_nested_dict()
