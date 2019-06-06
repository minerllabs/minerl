import random
from typing import List

import gym
import gym.spaces
import numpy as np

class Enum(gym.spaces.Discrete):
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
            elif action < super().n:
                return action
        except ValueError:
            raise ValueError("\"{}\" not valid ENUM value in values {}".format(action, self.values))
        finally:
            # TODO support more action formats through np.all < super().n
            raise ValueError("minerl.spaces.Enum: action must be of type str or int")

    def __len__(self):
        return len(self.values)