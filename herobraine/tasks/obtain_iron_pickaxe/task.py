from typing import List

import herobraine
import herobraine.hero.handlers as handlers
from herobraine.task import Task
import herobraine.env_specs


class ObtainIronPickaxe(Task):
    def __init__(self, name, resolution, episode_length, ms_per_tick, no_pitch=False):
        self.resolution = tuple(resolution)
        self.ms_per_tick = ms_per_tick
        self.episode_len = episode_length
        self.no_pitch = no_pitch
        self.env_spec = herobraine.env_specs.ObtainIronPickaxe()
        super().__init__(name, self.env_spec)

    def get_filter(self, source):
        pass

    def get_mission_file(self) -> str:
        return "./obtain_iron_pickaxe.xml"
