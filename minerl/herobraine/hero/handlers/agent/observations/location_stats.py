# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import jinja2
from typing import List

from minerl.herobraine.hero.handlers.translation import KeymapTranslationHandler, TranslationHandlerGroup
import minerl.herobraine.hero.mc as mc
from minerl.herobraine.hero import spaces
import numpy as np

__all__ = ['ObservationFromCurrentLocation']


class ObservationFromCurrentLocation(TranslationHandlerGroup):
    """
    Includes the current biome, how likely rain and snow are there, as well as the current light level, how bright the
    sky is, and if the player can see the sky.

    Also includes x, y, z, roll, and pitch
    """

    def xml_template(self) -> str:
        return str("""<ObservationFromFullStats/>""")

    def to_string(self) -> str:
        return "location_stats"

    def __init__(self):
        super(ObservationFromCurrentLocation, self).__init__(
            handlers=[
                _SunBrightnessObservation(),
                _SkyLightLevelObservation(),
                _LightLevelObservation(),
                _CanSeeSkyObservation(),
                _BiomeRainfallObservation(),
                _BiomeTemperatureObservation(),
                _IsRainingObservation(),
                # TODO _BiomeNameObservation(),
                _BiomeIDObservation(),
                _PitchObservation(),
                _YawObservation(),
                _XPositionObservation(),
                _YPositionObservation(),
                _ZPositionObservation(),
                _SeaLevelObservation()
            ]
        )


class _FullStatsObservation(KeymapTranslationHandler):
    def to_hero(self, x) -> int:
        for key in self.hero_keys:
            x = x[key]
        return x

    def __init__(self, key_list: List[str], space=None, default_if_missing=None):
        if space is None:
            if 'achievement' == key_list[0]:
                space = spaces.Box(low=0, high=1, shape=(), dtype=np.int)
            else:
                space = spaces.Box(low=0, high=np.inf, shape=(), dtype=np.int)
        if default_if_missing is None:
            default_if_missing = np.zeros((), dtype=np.float)

        super().__init__(hero_keys=key_list, univ_keys=key_list, space=space,
                         default_if_missing=default_if_missing)

    def xml_template(self) -> str:
        return str("""<ObservationFromFullStats/>""")


class _SunBrightnessObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['sun_brightness'], space=spaces.Box(low=0.0, high=1.0, shape=(), dtype=np.float),
                         default_if_missing=0.94)


class _SkyLightLevelObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['sky_light_level'], space=spaces.Box(low=0.0, high=1.0, shape=(), dtype=np.float),
                         default_if_missing=0.71)


class _XPositionObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['xpos'], space=spaces.Box(low=-640000.0, high=640000.0, shape=(), dtype=np.float),
                         default_if_missing=0.0)


class _YPositionObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['ypos'], space=spaces.Box(low=-640000.0, high=640000.0, shape=(), dtype=np.float),
                         default_if_missing=0.0)


class _ZPositionObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['zpos'], space=spaces.Box(low=-640000.0, high=640000.0, shape=(), dtype=np.float),
                         default_if_missing=0.0)


class _PitchObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['pitch'], space=spaces.Box(low=-180.0, high=180.0, shape=(), dtype=np.float),
                         default_if_missing=0.0)


class _YawObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['yaw'], space=spaces.Box(low=-180.0, high=180.0, shape=(), dtype=np.float),
                         default_if_missing=0.0)


class _BiomeIDObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['biome_id'],
                         space=spaces.Box(low=0, high=167, shape=(), dtype=np.int),
                         default_if_missing=0)


class _BiomeRainfallObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['biome_rainfall'],
                         space=spaces.Box(low=0.0, high=1.0, shape=()),
                         default_if_missing=0.5)


class _BiomeTemperatureObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['biome_temperature'],
                         space=spaces.Box(low=0.0, high=1.0, shape=()),
                         default_if_missing=0.5)


class _SeaLevelObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['sea_level'],
                         space=spaces.Box(low=0.0, high=255, shape=(), dtype=np.int),
                         default_if_missing=63)


class _LightLevelObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['light_level'],
                         space=spaces.Box(low=0.0, high=15, shape=(), dtype=np.int),
                         default_if_missing=15)


class _IsRainingObservation(_FullStatsObservation):
    def __init__(self):
        super().__init__(key_list=['is_raining'],
                         space=spaces.Box(low=0, high=1, shape=(), dtype=np.int),
                         default_if_missing=0)


class _CanSeeSkyObservation(_FullStatsObservation):
    def to_hero(self, x):
        for key in self.hero_keys:
            x = x[key]
        return np.eye(2)[x]

    def __init__(self):
        super().__init__(key_list=['can_see_sky'],
                         space=spaces.Box(low=0, high=1, shape=(), dtype=np.int),
                         default_if_missing=1)
