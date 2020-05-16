from abc import ABC, abstractmethod

class WrapperAct(ABC):
    def __init__(self, actionables):
        self.actionables = actionables
    @abstractmethod
    def get_act_space(self):
        raise NotImplementedError()
    @abstractmethod
    def convert_act(self, net_act):
        raise NotImplementedError()
    @abstractmethod
    def convert_acts(self, net_acts):
        raise NotImplementedError()
