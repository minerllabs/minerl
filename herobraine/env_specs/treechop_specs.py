from typing import List

import herobraine
import herobraine.hero.handlers as handlers
from herobraine.env_specs.env_spec import EnvSpec


class Treechop(EnvSpec):
    def __init__(self, name='MineRLTreechop-v0'):
        self.resolution = tuple((64, 64))
        self.episode_len = 400
        super().__init__(name, self.resolution)

    @staticmethod
    def is_from_folder(folder: str) -> bool:
        return folder == 'survivaltreechop'

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.EpisodeLength(self.episode_len),
            handlers.RewardForCollectingItems(
                {"log": 1.0}
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
        ]
        actionables += [handlers.MouseAction("pitch", "cameraPitch")]
        actionables += [handlers.MouseAction("turn", "cameraYaw")]
        return actionables
