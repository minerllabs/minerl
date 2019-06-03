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
    def __init__(self, *values: str):
        super().__init__(len(values))
        self.values = values

    def sample(self):
        return super().sample()

    def __getitem__(self, action):
        try:
            if isinstance(action, str):
                return self.values.index(action)
            elif action < super().n:
                return action
        except ValueError:
            raise ValueError("\"{}\" not valid ENUM value in values {}".format(action, self.values))
        finally:
            # TODO support more action formats through np.all < super().n
            raise ValueError("minerl.spaces.Enum: action must be of type str or int")

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


