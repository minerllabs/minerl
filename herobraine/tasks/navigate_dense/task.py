from typing import List

import herobraine
import herobraine.hero.handlers as handlers
from herobraine.task import Task
import herobraine.env_specs

class NavigateDenseTask(Task):
    def __init__(self, name, resolution, episode_length, ms_per_tick, no_pitch=False,
                 min_radius=64, max_radius=64, randomize_compass_target=False, 
                 dense_reward=False, observe_distance=False):
        self.resolution = tuple(resolution)
        self.ms_per_tick = ms_per_tick
        self.episode_len = episode_length
        self.no_pitch = no_pitch
        self.observe_distance = observe_distance
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.dense_reward = dense_reward
        self.randomize_compass_target = randomize_compass_target
        self.env_spec = herobraine.env_specs.NavigateDense()
        super().__init__(name, self.env_spec)


    def get_filter(self, source):
        pass

    def get_mission_file(self) -> str:
        return "navigation.xml"
