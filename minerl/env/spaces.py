import random
from typing import List

import gym
import gym.spaces
import numpy as np


class StringActionSpace(gym.spaces.Discrete):
    """Malmo actions as their strings."""
    def __init__(self):
        gym.spaces.Discrete.__init__(self, 1)

    def __getitem__(self, action):
        return action



class Enum(gym.spaces.Discrete):
    """
    An enum space. It can either be the enum string or a integer.
    """
    def __init__(self, *values : List[str]):
        super().__init__(len(values))
        self.values = values

    def sample(self):
        return super().sample() 

    def __getitem__(self, action):
        return index(self.values[action])

    def __len__(self):
        return len(self.values)



class ActionSpace(gym.spaces.Discrete):
    """Malmo actions as gym action space"""
    def __init__(self, actions):
        self.actions = actions
        gym.spaces.Discrete.__init__(self, len(self.actions))

    def sample(self):
        return random.randint(1, len(self.actions)) - 1

    def __getitem__(self, action):
        return self.actions[action]

    def __len__(self):
        return len(self.actions)


