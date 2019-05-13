import random
import string

import gym
import gym.spaces
import numpy as np


class Text(gym.Space):
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


class List(gym.Space):
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


class DiscreteRange(gym.spaces.Discrete):
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
