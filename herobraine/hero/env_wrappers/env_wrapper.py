import numpy as np
import gym
from gym.spaces.tuple_space import Tuple

from herobraine.episodes import Episodes
from herobraine.hero import InstanceManager, AgentHandler
from herobraine import hero

class HeroEnvWrapper(gym.Env):
    def __init__(self, experiment, wrap_act, wrap_obs, num_envs=1):
        self.wrap_act = wrap_act
        self.wrap_obs = wrap_obs
        self.action_space = self.wrap_act.get_act_space()
        self.observation_space = self.wrap_obs.get_obs_space()

        self.num_obs_heads = 1
        if isinstance(self.observation_space, Tuple):
            self.num_obs_heads = len(self.observation_space.spaces)
        
        # Seriously lets take a moment here to be like... why does openai
        # baselines call two different forms of "num environments" in two
        # different locations? ugh
        self.nenvs = num_envs
        self.num_envs = num_envs

        self.task = experiment._main_task
        self.experiment = experiment
        self.ep = None
        self.episodes_context = None
        
    def reset(self):
        if self.ep is not None:
            self.ep.end()
        if self.episodes_context is not None:
            self.episodes_context.__exit__(None, None, None)
        self.episodes_context = self.experiment.get_episodes(self.task)
        self.ep = self.episodes_context.__enter__()
        self.elapsed = 0
        return self.wrap_obs.convert_multiple_obs((self.ep.start(), self.elapsed))
        
    def step(self, action):
        try:
            self.elapsed += 1
            s,r,d,i = self.ep.step(self.wrap_act.convert_acts(action))
            self.last_s = self.wrap_obs.convert_multiple_obs((s, self.elapsed))
        except StopIteration:
            r = np.zeros(self.num_envs)
            d = np.full(self.num_envs, True)
            i = None
        return self.last_s, r, d, i

    def pause(self):
        if self.ep is not None:
            self.ep.pause()

    def unpause(self):
        if self.ep is not None:
            self.ep.unpause()
