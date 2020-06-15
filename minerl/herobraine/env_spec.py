from abc import abstractmethod
# import minerl.env.spaces as spaces
import gym
import os
import abc

# TODO:
MISSIONS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "env_specs", "missions")

from minerl.herobraine.hero import spaces


class EnvSpec(abc.ABC):
    ENTRYPOINT = 'minerl.env:MineRLEnv'

    def __init__(self, name, xml, max_episode_steps=None, reward_threshold=None):
        self.name = name
        self.xml = xml
        self.max_episode_steps = max_episode_steps
        self.reward_threshold = reward_threshold

        self.observables = self.create_observables()
        self.actionables = self.create_actionables()
        # check that the observables (list) have no duplicate to_strings
        assert len([o.to_string() for o in self.observables]) == len(set([o.to_string() for o in self.observables]))
        assert len([a.to_string() for a in self.actionables]) == len(set([a.to_string() for a in self.actionables]))

        self.mission_handlers = self.create_mission_handlers()

        self._observation_space = self.create_observation_space()
        self._action_space = self.create_action_space()

    @property
    def observation_space(self):
        return self._observation_space

    @property
    def action_space(self):
        return self._action_space

    def to_string(self):
        return self.name

    @abstractmethod
    def is_from_folder(self, folder: str) -> bool:
        raise NotImplementedError('subclasses must override is_from_folder()!')

    @abstractmethod
    def create_mission_handlers(self):
        raise NotImplementedError('subclasses must override create_mission_handlers()!')

    @abstractmethod
    def create_observables(self):
        raise NotImplementedError('subclasses must override create_observables()!')

    @abstractmethod
    def create_actionables(self):
        raise NotImplementedError('subclasses must override create_actionables()!')

    @abstractmethod
    def determine_success_from_rewards(self, rewards: list) -> bool:
        raise NotImplementedError('subclasses must override determine_success_from_rewards()')

    def create_observation_space(self):
        # Todo: handle nested dict space.
        return spaces.Dict({
            o.to_string(): o.space for o in self.observables
        })

    def create_action_space(self):
        return spaces.Dict({
            a.to_string(): a.space for a in self.actionables
        })

    @abstractmethod
    def get_docstring(self):
        return NotImplemented

    def register(self):
        reg_spec = dict(
            id=self.name,
            entry_point=EnvSpec.ENTRYPOINT,
            kwargs={
                'observation_space': self.observation_space,
                'action_space': self.action_space,
                'docstr': self.get_docstring(),
                'xml': os.path.join(MISSIONS_DIR, self.xml),
                'env_spec': self,
            },
            max_episode_steps=self.max_episode_steps,
        )
        if self.reward_threshold:
            reg_spec.update(dict(reward_threshold=self.reward_threshold))

        gym.register(**reg_spec)

    def __repr__(self):
        """
        Prints the class, name, observation space, and action space of the handler.
        """
        return '{}-{}-spaces({},{})'.format(self.__class__.__name__, self.name, self.observation_space,
                                            self.action_space)
