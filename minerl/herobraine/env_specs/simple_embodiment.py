# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import abc
from abc import ABC
from minerl.herobraine.hero.handlers.translation import TranslationHandler
from minerl.herobraine.hero.handler import Handler

from minerl.herobraine.hero import handlers
from minerl.herobraine.hero.mc import INVERSE_KEYMAP
from minerl.herobraine.env_spec import EnvSpec

from typing import List

SIMPLE_KEYBOARD_ACTION = [
    "forward",
    "back",
    "left",
    "right",
    "jump",
    "sneak",
    "sprint",
    "attack"
]


class SimpleEmbodimentEnvSpec(EnvSpec, ABC):
    """
    A simple base environment from which all other simple envs inherit.
    """

    def __init__(self, name, *args, resolution=(64, 64), **kwargs):
        self.resolution = resolution
        super().__init__(name, *args, **kwargs)

    def create_observables(self) -> List[TranslationHandler]:
        return [
            handlers.POVObservation(self.resolution),
        ]

    def create_actionables(self) -> List[TranslationHandler]:
        """
        Simple envs have some basic keyboard control functionality, but
        not all.
        """
        return [
                   handlers.KeybasedCommandAction(k, v) for k, v in INVERSE_KEYMAP.items()
                   if k in SIMPLE_KEYBOARD_ACTION
               ] + [
                   handlers.CameraAction()
               ]

    def create_monitors(self) -> List[TranslationHandler]:
        return []  # No base monitor needed
