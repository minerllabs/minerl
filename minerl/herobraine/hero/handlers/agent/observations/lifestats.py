# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import jinja2
from minerl.herobraine.hero.handlers.translation import KeymapTranslationHandler, TranslationHandlerGroup
import minerl.herobraine.hero.mc as mc
import minerl.herobraine.hero.spaces as spaces
import numpy as np

__all__ = ['ObservationFromLifeStats']


class ObservationFromLifeStats(TranslationHandlerGroup):
    """Groups all of the lifestats observations together to correspond to one XML element."""

    def to_string(self) -> str:
        return "life_stats"

    def __init__(self):
        super(ObservationFromLifeStats, self).__init__(
            handlers=[
                _IsAliveObservation(),
                _LifeObservation(),
                _ScoreObservation(),
                _FoodObservation(),
                _SaturationObservation(),
                _XPObservation(),
                _BreathObservation(),
            ]
        )

    def xml_template(self) -> str:
        return str("""<ObservationFromFullStats/>""")


class LifeStatsObservation(KeymapTranslationHandler):
    def to_hero(self, x) -> str:
        pass

    def __init__(self, hero_keys, univ_keys, space, default_if_missing=None):
        self.hero_keys = hero_keys
        self.univ_keys = univ_keys
        super().__init__(hero_keys=hero_keys, univ_keys=['life_stats'] + univ_keys, space=space,
                         default_if_missing=default_if_missing)

    def xml_template(self) -> str:
        return str("""<ObservationFromFullStats/>""")


class _IsAliveObservation(LifeStatsObservation):
    """
    Handles is_alive observation. Initial value is True (alive)
    """

    def __init__(self):
        keys = ['is_alive']
        super().__init__(hero_keys=keys, univ_keys=keys,
                         space=spaces.Box(low=False, high=True, shape=(), dtype=np.bool),
                         default_if_missing=True)


class _LifeObservation(LifeStatsObservation):
    """
    Handles life observation / health observation. Its initial value on world creation is 20 (full bar)
    """

    def __init__(self):
        keys = ['life']
        super().__init__(hero_keys=keys, univ_keys=keys,
                         space=spaces.Box(low=0, high=mc.MAX_LIFE, shape=(), dtype=np.float),
                         default_if_missing=mc.MAX_LIFE)


class _ScoreObservation(LifeStatsObservation):
    """
    Handles score observation
    """

    def __init__(self):
        keys = ['score']
        super().__init__(univ_keys=keys, hero_keys=keys,
                         space=spaces.Box(low=0, high=mc.MAX_SCORE, shape=(), dtype=np.int),
                         default_if_missing=0)


class _FoodObservation(LifeStatsObservation):
    """
    Handles food_level observation representing the player's current hunger level, shown on the hunger bar. Its initial
    value on world creation is 20 (full bar) - https://minecraft.gamepedia.com/Hunger#Mechanics
    """

    def __init__(self):
        super().__init__(hero_keys=['food'], univ_keys=['food'],
                         space=spaces.Box(low=0, high=mc.MAX_FOOD, shape=(), dtype=np.int),
                         default_if_missing=mc.MAX_FOOD)


class _SaturationObservation(LifeStatsObservation):
    """
    Returns the food saturation observation which determines how fast the hunger level depletes and is controlled by the
    kinds of food the player has eaten. Its maximum value always equals foodLevel's value and decreases with the hunger
    level. Its initial value on world creation is 5. - https://minecraft.gamepedia.com/Hunger#Mechanics
    """

    def __init__(self):
        super().__init__(hero_keys=['saturation'], univ_keys=['saturation'],
                         space=spaces.Box(low=0, high=mc.MAX_FOOD_SATURATION, shape=(),
                                          dtype=np.float), default_if_missing=5.0)


class _XPObservation(LifeStatsObservation):
    """
    Handles observation of experience points 1395 experience corresponds with level 30
    - see https://minecraft.gamepedia.com/Experience for more details
    """

    def __init__(self):
        keys = ['xp']
        super().__init__(hero_keys=keys, univ_keys=keys,
                         space=spaces.Box(low=0, high=mc.MAX_XP, shape=(), dtype=np.int),
                         default_if_missing=0)


class _BreathObservation(LifeStatsObservation):
    """
    Handles observation of breath which tracks the amount of air remaining before beginning to suffocate
    """

    def __init__(self):
        super().__init__(hero_keys=['air'], univ_keys=['air'], space=spaces.Box(low=0, high=mc.MAX_BREATH, shape=(),
                                                                                dtype=np.int), default_if_missing=300)

# class DeathObservation(TranslationHandler):

#     def to_string(self):
#         return 'alive'

#     def from_hero(self, obs_dict):
#         return obs_dict["IsAlive"] if "IsAlive" in obs_dict else True
