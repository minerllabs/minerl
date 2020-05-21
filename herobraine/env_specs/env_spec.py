
from abc import abstractmethod
import minerl.env.spaces as spaces
import gym
import os
# TODO: Make this minerl spaces
from minerl.env.core import missions_dir


class EnvSpec:
    ENTRYPOINT = 'minerl.env:MineRLEnv'

    def __init__(self, name, xml, max_episode_steps=None, reward_threshold=None):
        self.name = name
        self.xml = xml
        self.max_episode_steps = max_episode_steps
        self.reward_threshold = reward_threshold

        self.observables = self.create_observables()
        self.actionables = self.create_actionables()
        self.mission_handlers = self.create_mission_handlers()

    def to_string(self):
        return self.name

    @abstractmethod
    def is_from_folder(folder: str) -> bool:
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
    def get_observation_space(self):
        # Todo: handle nested dict space.
        
        ss = {
            o.to_string(): o.space for o in self.observables if not hasattr(o, 'hand')
        }
        try:
            ss.update({
                'equipped_items': spaces.Dict({
                    'mainhand': spaces.Dict({
                         o.to_string(): o.space for o in self.observables if hasattr(o, 'hand')
                    })
                })
            })
        except Exception as e:
            print(e)
            pass
            
        return spaces.Dict(spaces=ss)

    def get_action_space(self):
        return spaces.Dict(spaces={
            a.to_string(): a.space for a in self.actionables
        })

    @abstractmethod
    def get_docstring(self):
        return NotImplemented

    def register(self):
        gym.register(
            id=self.name,
            entry_point=EnvSpec.ENTRYPOINT,
            kwargs={
                'observation_space': self.get_observation_space(),
                'action_space': self.get_action_space(),
                'docstr': self.get_docstring(),
                'xml': os.path.join(missions_dir, self.xml)
            },
            max_episode_steps=self.max_episode_steps,
            reward_threshold=self.reward_threshold,
        )
        
        