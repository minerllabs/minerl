from typing import List

import herobraine.hero.handlers as handlers
import herobraine.env_specs as env_specs
from herobraine.task import Task


class TreechopTask(Task):
    def __init__(self, name, resolution, episode_length, ms_per_tick, no_pitch=False):
        self.resolution = tuple(resolution)
        self.ms_per_tick = ms_per_tick
        self.episode_len = episode_length
        self.no_pitch = no_pitch
        self.env_spec = env_specs.Treechop()
        super().__init__(name, self.env_spec)


    def get_filter(self, source):
        pass

    def get_mission_file(self) -> str:
        return "./treechop.xml"