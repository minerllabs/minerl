from abc import ABC, abstractmethod

class WrapperObs(ABC):
    def __init__(self):
        pass
    @abstractmethod
    def get_obs_space(self):
        raise NotImplementedError()
    @abstractmethod
    def convert_obs(self, raw_obs):
        raise NotImplementedError()
    @abstractmethod
    def convert_multiple_obs(self, multiple_obs):
        raise NotImplementedError()
