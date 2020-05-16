from abc import ABC, abstractmethod
from typing import Any

from gym import Space

from herobraine.episode import Episode
from herobraine.hero.agent_handler import HandlerCollection
from herobraine.task import Task


class Vectorizer(ABC):
    """
    Vectorizes an episode in a convenient format for ML.

    Learning Procedure <- Vectorizer <- Episode(Task)
    Learning Procedure <- tf.data.iter <- Vectorizer <- AgentHandlers <- tf.data.slicers :).


    """
    def __init__(self, task : Task):
        self.task = task
        self._action_space = self.create_vector_action_space(task)
        self._observation_space = self.create_vector_observation_space(task)


    @abstractmethod
    def vector_from_observables(self, obs: HandlerCollection) -> Any:
        """
        Vectorizes the observation
        :param obs:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def actionables_from_vector(self, act : Any) -> HandlerCollection:
        """
        Vectorizes the action.
        Using self.task.actionables will be useful in this case.
        :param obs:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def vector_from_actionables(selfs, actionables: HandlerCollection):
        """
        Converts a list of actionables to a vectror. Used in loading data from disk.
        :param actionables:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def create_vector_action_space(self, task) -> Space:
        raise NotImplementedError()

    @abstractmethod
    def create_vector_observation_space(self, task) -> Space:
        raise NotImplementedError()


    ####################
    #### Properties ####
    ####################
    @property
    def action_space(self):
        """
        The actionspace of the vectorizer.
        :return:
        """
        return self.action_space


    @property
    def state_space(self):
        """
        The state space of the vectorizer
        :return:
        """
        return self.state_space


