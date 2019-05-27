import gym
import gym.spaces
import random
import numpy as np


class StringActionSpace(gym.spaces.Discrete):
    """Malmo actions as their strings."""
    def __init__(self):
        gym.spaces.Discrete.__init__(self, 1)

    def __getitem__(self, action):
        return action


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


class VisualObservationSpace(gym.spaces.Box):
    """Space for visual observations: width x height x depth as a flat array.
    Where depth is 3 or 4 if encoding scene depth.
    """
    def __init__(self, width, height, depth):
        gym.spaces.Box.__init__(self,
                                low=np.iinfo(np.uint8).min, high=np.iinfo(np.uint8).max,
                                shape=(height, width, depth), dtype=np.uint8)
