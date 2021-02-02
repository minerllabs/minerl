import abc
from abc import ABC
from minerl.herobraine.hero.handlers.translation import TranslationHandler
from minerl.herobraine.hero.handler import Handler

from minerl.herobraine.hero import handlers
from minerl.herobraine.hero.handlers import POVObservation, CameraAction, KeybasedCommandAction
from minerl.herobraine.hero.mc import INVERSE_KEYMAP
from minerl.herobraine.env_spec import EnvSpec

from typing import List

KEYBOARD_ACTIONS = [
    "forward",
    "back",
    "left",
    "right",
    "jump",
    "sneak",
    "sprint",
    "attack",
    "use",
    "drop",
    "inventory"
]


class HumanControlEnvSpec(EnvSpec, ABC):
    """
    A simple base environment from which all other simple envs inherit.
    """

    def __init__(self, name, *args, resolution=(640, 480), **kwargs):
        self.resolution = resolution
        super().__init__(name, *args, **kwargs)

    def create_observables(self) -> List[TranslationHandler]:
        return [
            POVObservation(self.resolution),
        ]

    def create_actionables(self) -> List[TranslationHandler]:
        """
        Simple envs have some basic keyboard control functionality, but
        not all.
        """
        return [
           KeybasedCommandAction(k, INVERSE_KEYMAP[k]) for k in KEYBOARD_ACTIONS
        ] + [
           KeybasedCommandAction(f"hotbar.{i}", INVERSE_KEYMAP[str(i)]) for i in range(1, 10)
        ] + CameraAction()

    def create_monitors(self) -> List[TranslationHandler]:
        return []  # No monitors by default!o

    def create_agent_start(self) -> List[Handler]:
        return [handlers.LowLevelInputsAgentStart()]
