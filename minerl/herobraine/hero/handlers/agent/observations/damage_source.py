# Copyright (c) 2021 All Rights Reserved
# Author: Brandon Houghton

from typing import List

from minerl.herobraine.hero.handlers.translation import (KeymapTranslationHandler,
                                                         TranslationHandlerGroup)
from minerl.herobraine.hero import spaces
import numpy as np

__all__ = ['ObservationFromDamageSource']


class ObservationFromDamageSource(TranslationHandlerGroup):
    """
    Includes the most recent damage event including the amount, type, location, and
    other properties.
    """

    def xml_template(self) -> str:
        return "<ObservationFromDamage/>"

    def to_string(self) -> str:
        return "damage_source"

    def __init__(self):
        super(ObservationFromDamageSource, self).__init__(
            handlers=[
                _HungerDamage(),
                _DamageAmount(),
                _IsDead(),
                # TODO implement str space processing for obs
                # _DamageType(),
                # _DeathMessage(),
            ]
        )


class _DamageSourceProperty(KeymapTranslationHandler):
    def to_hero(self, x) -> int:
        for key in self.hero_keys:
            x = x[key]
        return x

    def __init__(self, key_list: List[str], space=None, default_if_missing=None):
        if space is None:
            space = spaces.Box(low=0, high=np.inf, shape=(), dtype=np.int)
        if default_if_missing is None:
            default_if_missing = np.zeros((), dtype=space.dtype)

        super().__init__(hero_keys=key_list, univ_keys=key_list, space=space,
                         default_if_missing=default_if_missing, ignore_missing=True)

    def xml_template(self) -> str:
        return "<ObservationFromDamageSource/>"


class _IsDead(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=['is_dead'],
            space=spaces.Box(low=0.0, high=1.0, shape=(), dtype=np.int),
        )


class _DamageAmount(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=['damage_amount'],
            space=spaces.Box(low=0.0, high=40.0, shape=(), dtype=np.float),
        )


# class _DamageType(_DamageSourceProperty):
#     def __init__(self):
#         super().__init__(key_list=['damage_type'], space=spaces.Text(shape=()),
#                          default_if_missing=np.str(""))
#
#
# class _DeathMessage(_DamageSourceProperty):
#     def __init__(self):
#         super().__init__(key_list=['death_message'], space=spaces.Text(shape=()),
#                          default_if_missing=np.str(""))


class _HungerDamage(_DamageSourceProperty):
    def __init__(self):
        super().__init__(
            key_list=['hunger_damage'],
            space=spaces.Box(low=0, high=20, shape=(), dtype=np.float),
        )

# TODO create the rest of the fields in ObservationFromDamageImplementation.java
