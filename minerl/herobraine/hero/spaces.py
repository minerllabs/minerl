import random
import string

import gym
import gym.spaces
import numpy as np

import random
from collections import OrderedDict
from typing import List

import gym
import gym.spaces
import numpy as np
import collections

import abc


class MineRLSpace(abc.ABC, gym.Space):
    """
    An interface for MineRL spaces.
    """

    @property
    def flattened(self) -> gym.spaces.Box:
        if not hasattr(self, '_flattened'):
            self._flattened = self.create_flattened_space()
        return self._flattened

    @abc.abstractmethod
    def no_op(self):
        pass

    @abc.abstractmethod
    def create_flattened_space(self):
        pass

    @abc.abstractmethod
    def flat_map(self, x):
        pass

    @abc.abstractmethod
    def unmap(self, x):
        pass

    def is_flattenable(self):
        return True


class Tuple(gym.spaces.Tuple, MineRLSpace):

    def no_op(self):
        raise NotImplementedError()

    def create_flattened_space(self):
        raise NotImplementedError()

    def flat_map(self, x):
        raise NotImplementedError()

    def unmap(self, x):
        raise NotImplementedError()


class Box(gym.spaces.Box, MineRLSpace):
    def __init__(self, *args,  normalizer_scale='linear', **kwargs):
        super(Box, self).__init__(*args, **kwargs)

        self._flat_low = self.low.flatten().astype(np.float64)
        self._flat_high = self.high.flatten().astype(np.float64)
        
        if normalizer_scale == 'log':
            self.max_log = np.log(1 + (self._flat_high - self._flat_low))
        else:
            assert normalizer_scale == 'linear', "only log and linear are supported"

        self.normalizer_scale = normalizer_scale

    CENTER = 0

    def no_op(self):
        return np.zeros(shape=self.shape).astype(self.dtype)

    def create_flattened_space(self):
        if len(self.shape) > 2:
            raise TypeError("Box spaces with 3D tensor shapes cannot be flattened.")
        else:
            return Box(low=self._flat_low, high=self._flat_high)

    def flat_map(self, x):
        flatx = x.reshape(list(x.shape[:-len(self.shape)]) + [np.prod(self.shape).astype(int)])
        if self.normalizer_scale == 'linear':
            return (flatx.astype(np.float64) - self._flat_low) / (self._flat_high - self._flat_low) - Box.CENTER
        elif self.normalizer_scale == 'log':
            return np.log(flatx.astype(np.float64) - self._flat_low + 1) / self.max_log - Box.CENTER

    def unmap(self, x):
        """
        Un-normalizes the flattened x to its original high and low.
        Then reshapes it back to the original shape.
        """
        low = x + Box.CENTER
        
        if self.normalizer_scale == 'linear':
            high = low * (self._flat_high - self._flat_low) + self._flat_low
        elif self.normalizer_scale == 'log':
            high = np.exp(low* self.max_log) -1 + self._flat_low

        reshaped =  high.reshape(list(x.shape[:-len(self.shape)]) + list(self.shape))
        if np.issubdtype(self.dtype, np.integer):
            return np.round(reshaped).astype(self.dtype)
        else:
            return reshaped.astype(self.dtype)

    def is_flattenable(self):
        return len(self.shape) <= 2

    def clip(self, x):
        # Clips the vector x between the vectors self.low and self.high.
        return np.clip(x, self.low, self.high)


    def __repr__(self):
        # Prints the name of the class and its information
        # Specifically, the shape, the max of self.high, and the min of self.low
        # :return: string representation of the Box
        return "Box(low={0}, high={1}, shape={2})".format(np.min(self.low), np.max(self.high), self.shape)




class Discrete(gym.spaces.Discrete, MineRLSpace):
    def __init__(self, *args, **kwargs):
        super(Discrete, self).__init__(*args, **kwargs)
        self.eye = np.eye(self.n, dtype=np.float32)

    def no_op(self):
        return 0

    def create_flattened_space(self):
        return Box(low=0, high=1, shape=(self.n,))

    def flat_map(self, x):
        return self.eye[x]

    def unmap(self, x):
        return np.array(np.argmax(x).flatten().tolist()[0], dtype=self.dtype)


class Enum(Discrete, MineRLSpace):
    """
    An enum space. It can either be the enum string or a integer.
    """

    def __init__(self, *values: str, default=None):
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
        if not isinstance(values, tuple):
            values = (values,)
        self.default = default if default is not None else values[0]
        super().__init__(len(values))
        self.values = np.array(sorted(values))
        self.value_map = dict(zip(values, range(len(values))))

    def sample(self) -> int:
        """Samples a random index for one of the enum types.

        ```
        x.sample() # A random nubmer in the half-open discrete interval [0, len(x.values))
        ````

        Returns:
            int:  A random index for one of the enum types.
        """
        return self.values[super().sample()]

    def flat_map(self, x):
        return super().flat_map(self[x])

    def unmap(self, x):
        return self.values[super().unmap(x)]


    def no_op(self):
        if self.default:
            return self.default
        else:
            return self.values[super().no_op()]

    def __getitem__(self, action):
        try:
            single_act = False
            if isinstance(action, str):
                single_act = True
                action = np.array([action])


            u,inv = np.unique(action,return_inverse = True)
            
            print(action, u, inv)
            inds = np.array([self.value_map[x] for x in u])[inv].reshape(action.shape)

            return inds if not single_act else inds.tolist()[0]

        except ValueError:
            raise ValueError("\"{}\" not valid ENUM value in values {}".format(action, self.values))

        # TODO support more action formats through np.all < super().n
        raise ValueError("spaces.Enum: action must be of type str or int")

    def __str__(self):
        return "Enum(" + ','.join(self.values) + ")"

    def __len__(self):
        return len(self.values)

    def contains(self, x):
        return x in self.values

    __contains__ = contains


# TODO: Vectorize containment?
class Dict(gym.spaces.Dict, MineRLSpace):
    def no_op(self):
        return OrderedDict([(k, space.no_op()) for k, space in self.spaces.items()])

    def create_flattened_space(self):
        shape = sum([s.flattened.shape[0] for s in self.spaces.values()
                     if s.is_flattenable()])
        return Box(low=0, high=1, shape=[shape], dtype=np.float32)

    def create_unflattened_space(self):
        # TODO Fix this really ugly hack for flattening.
        # Needs to be a generic design that's simple that 
        # encapsulates unflattenable or not;
        # First calss support for unflattenable spaces..
        return Dict({
            k: (
                v.unflattened if hasattr(v, 'unflattened')
                else v
            ) for k, v in self.spaces.items() if not v.is_flattenable()
        })

    @property
    def unflattened(self):
        """
        Returns the unflatteneable part of the space.
        """
        if not hasattr(self, "_unflattened"):
            self._unflattened = self.create_unflattened_space()
        return self._unflattened

    def flat_map(self, x):
        try:
            return np.concatenate(
                [v.flat_map(x[k]) if k in x else v.flat_map(v.no_op()) for (k, v) in (self.spaces.items()) if
                (v.is_flattenable())],
                axis=-1
            )
        except ValueError:
            # No flattenable handlers found
            return np.array([])

    def unflattenable_map(self, x: OrderedDict) -> OrderedDict:
        """
        Selects the unflattened part of x
        """
        return OrderedDict({
            k: (
                v.unflattenable_map(x[k]) if hasattr(v, 'unflattenable_map')
                else x[k]
            )
            # filter
            for k, v in (self.spaces.items()) if not v.is_flattenable()
        })

    def unmap(self, x : np.ndarray, skip=False) -> OrderedDict:
        unmapped = collections.OrderedDict()
        cur_index = 0
        for k, v in self.spaces.items():
            if v.is_flattenable():
                unmapped[k] = v.unmap(x[..., cur_index:cur_index + v.flattened.shape[0]])
                cur_index += v.flattened.shape[0]
            elif not skip:
                raise ValueError('Dict space contains is_flattenable values - unmap with unmap_mixed')

        return unmapped

    def unmap_mixed(self, x: np.ndarray, aux: OrderedDict):
        # split x
        unmapped = collections.OrderedDict()
        cur_index = 0
        for k, v in self.spaces.items():
            if v.is_flattenable():
                try:
                    unmapped[k] = v.unmap_mixed(x[..., cur_index:cur_index + v.flattened.shape[0]], aux[k])
                except (KeyError, AttributeError):
                    unmapped[k] = v.unmap(x[..., cur_index:cur_index + v.flattened.shape[0]])
                cur_index += v.flattened.shape[0]
            else:
                unmapped[k] = aux[k]

        return unmapped


class MultiDiscrete(gym.spaces.MultiDiscrete, MineRLSpace):
    def __init__(self, *args, **kwargs):
        super(MultiDiscrete, self).__init__(*args, **kwargs)
        self.eyes = [np.eye(n, dtype=np.float32) for n in self.nvec]

    def no_op(self):
        return (np.zeros(self.nvec.shape) * self.nvec).astype(self.dtype)

    def create_flattened_space(self):
        return Box(low=0, high=1, shape=[
            np.sum(self.nvec)
        ])

    def flat_map(self, x):
        return np.concatenate(
            [self.eyes[i][x[..., i]] for i in range(len(self.nvec))],
        axis=-1)

    def unmap(self, x):
        cur_index = 0
        out = []
        for n in self.nvec:
            out.append(np.argmax(x[..., cur_index:cur_index + n], axis=-1)[...,np.newaxis])
            cur_index += n
        return np.concatenate(out,axis=-1).astype(self.dtype)


class Text(gym.Space):
    """
    # TODO:
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

    def is_flattenable(self):
        return False


class DiscreteRange(Discrete):
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
        super().__init__(end - begin)

    def sample(self):
        return super().sample() + self.begin

    def contains(self, x):
        return super().contains(x - self.begin)

        
    __contains__ = contains

    def no_op(self):
        return self.begin

    def create_flattened_space(self):
        return Box(low=0, high=1, shape=(self.n,))

    def flat_map(self, x):
        return self.eye[x - self.begin]

    def unmap(self, x):
        return np.array(np.argmax(x, axis=-1) + self.begin, dtype=self.dtype)

    def __repr__(self):
        return "DiscreteRange({}, {})".format(self.begin, self.n + self.begin)

    def __eq__(self, other):
        return self.n == other.n and self.begin == other.begin
