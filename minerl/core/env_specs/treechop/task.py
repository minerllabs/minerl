from typing import List

import herobraine
import herobraine.hero.handlers as handlers
from herobraine.task import Task


class TreechopTask(Task):
    def __init__(self, name, resolution, episode_length, ms_per_tick, no_pitch=False):
        self.resolution = tuple(resolution)
        self.ms_per_tick = ms_per_tick
        self.episode_len = episode_length
        self.no_pitch = no_pitch
        super().__init__(name)


    def get_filter(self, source):
        pass

    def get_mission_file(self) -> str:
        return "./treechop.xml"

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.TickHandler(self.ms_per_tick),
            handlers.EpisodeLength(self.episode_len),
            handlers.RewardForCollectingItems(
                "log", 1.0
            )
        ]

    def create_observables(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.POVObservation(self.resolution),
            handlers.FlatInventoryObservation(["log:0", "log:1", "log:2", "log:3", "log2:0", "log2:1"])
        ]

    def create_actionables(self) -> List[herobraine.hero.AgentHandler]:
        actionables = [
            handlers.KeyboardAction("move", "S", "W"),
            handlers.KeyboardAction("strafe", "A", "D"),
            handlers.KeyboardAction("jump", "SPACE"),
            handlers.KeyboardAction("crouch", "SHIFT"),
            handlers.KeyboardAction("attack", "BUTTON0"),
            handlers.KeyboardAction("use", "BUTTON1"),
        ]
        if not self.no_pitch:
            actionables += [handlers.MouseAction("pitch", "cameraPitch")]
        actionables += [handlers.MouseAction("turn", "cameraYaw")]
        return actionables
