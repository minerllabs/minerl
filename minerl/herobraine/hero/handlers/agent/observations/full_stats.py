# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import jinja2
from minerl.herobraine.hero.handlers.translation import KeymapTranslationHandler, TranslationHandlerGroup
import minerl.herobraine.hero.mc as mc
import minerl.herobraine.hero.spaces as spaces
import numpy as np

__all__ = ['ObservationFromFullStats']


class ObservationFromFullStats(TranslationHandlerGroup):
    """
    Groups all of the biome observations together to correspond to one XML element.

    Includes the current biome, how likely rain and snow are there, as well as the current light level, how bright the
    sky is, and if the player can see the sky."""

    def to_string(self) -> str:
        return "fullStats"

    def __init__(self):
        super(ObservationFromFullStats, self).__init__(
            handlers=[
                _CanSeeSkyObservation(),
                _LightLevelObservation(),
                _SkyLightLevelObservation(),
                _SunBrightnessObservation()
            ]
        )

    def xml_template(self) -> str:
        return str("""<ObservationFromFullStats/>""")



class ObservationFromFullStats(KeymapTranslationHandler):
    def to_hero(self, x) -> str:
        pass

    def __init__(self, dict_key, space, default_if_missing=None):
        super().__init__(hero_keys=['currrent_biome', dict_key], univ_keys=['currrent_biome', dict_key], space=space,
                         default_if_missing=default_if_missing)

    def xml_template(self) -> str:
        return str("""<ObservationFromFullStats/>""")


class _StatObservation(ObservationFromFullStats):
    """
    Handles current biome observation. Represents a string coresoponding to the current biome of the agent
        See line 543 of Biome.java for an enumeration of the current java biomes, or EXPLORATION_BIOMES_LIST
    """

    def __init__(self):
        super().__init__(dict_key='biome_name',
                         space=spaces.Text(shape=()))

class _AchievementObservation(ObservationFromFullStats):
    """
    A abstract class for achievement status. Given the large number of keys with little change we implement these as a
    their default value of false when not present
    """

    def __init__(self, achievement_key : str):
        super().__init__(dict_keys=['achievement', achievement_key],
                         space=spaces.Discrete(2),
                         default_if_missing=np.eye(2)[0,:])

class _BlockStatObservation(ObservationFromFullStats):
    """
    """

    def __init__(self):
        super().__init__(dict_key='biome_temperature',
                         space=spaces.Box(low=0.0, high=1.0, shape=()),
                         default_if_missing=0.5)

class _ItemStatObservation(ObservationFromFullStats):
    """
    """

    def __init__(self):
        super().__init__(dict_key='biome_rainfall',
                         space=spaces.Box(low=0.0, high=1.0, shape=()),
                         default_if_missing=0.5)

class _LightLevelObservation(ObservationFromFullStats):
    def __init__(self):
        super().__init__(dict_key='light_level', space=spaces.Discrete(15), default_if_missing=7)

class _CanSeeSkyObservation(ObservationFromFullStats):
    def __init__(self):
        super().__init__(dict_key='can_see_sky', space=spaces.Discrete(2), default_if_missing=1)

class _SunBrightnessObservation(ObservationFromFullStats):
    def __init__(self):
        super().__init__(dict_key='sun_brightness', space=spaces.Box(low=0.0, high=1.0, shape=()), default_if_missing=0.5)

class _SkyLightLevelObservation(ObservationFromFullStats):
    def __init__(self):
        super().__init__(dict_key='sky_light_level', space=spaces.Discrete(15), default_if_missing=7)

