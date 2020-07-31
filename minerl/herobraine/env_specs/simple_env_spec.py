import abc
from abc import ABC
from minerl.herobraine.hero.handler import Handler

import minerl

from minerl.herobraine.hero import handlers
from minerl.herobraine.hero.mc import INVERSE_KEYMAP
from minerl.herobraine.env_spec import EnvSpec

from typing import List


class SimpleEnvSpec(EnvSpec, ABC):
    """
    A simple base environment from which all othe simple envs inherit.
    """
    STANDARD_KEYBOARD_ACTIONS = [
        "forward",
        "back",
        "left",
        "right",
        "jump",
        "sneak",
        "sprint",
        "attack"
    ]

    def __init__(self, name, xml, *args, resolution=(64,64), **kwargs):
        self.resolution = resolution
        super().__init__(name, xml, *args, **kwargs)

    def create_observables(self) -> List[minerl.herobraine.hero.AgentHandler]:
        return [
            handlers.POVObservation(self.resolution)
        ]
    
    def create_actionables(self) -> List[minerl.herobraine.hero.AgentHandler]:
        """
        Simple envs have some basic keyboard control functionality, but
        not all.
        """
        return [
            handlers.KeyboardAction(k, v) for k,v in INVERSE_KEYMAP.items()
            if k in SimpleEnvSpec.STANDARD_KEYBOARD_ACTIONS
        ] + [
            handlers.Camera()
        ]
