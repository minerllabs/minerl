"""
    Defines observations from damage source.
"""
import math
from collections import defaultdict
import jinja2
import numpy as np

from minerl.herobraine.hero import spaces

from minerl.herobraine.hero.handlers.translation import (
    KeymapTranslationHandler,
    TranslationHandlerGroup,
)


__all__ = ["ObservationFromDamageSource"]

DAMAGE_TYPE_KEYS = [
    "none",
    "inFire",
    "lightningBolt",
    "onFire",
    "lava",
    "hotFloor",
    "inWall",
    "cramming",
    "drown",
    "starve",
    "cactus",
    "fall",
    "flyIntoWall",
    "outOfWorld",
    "generic",
    "magic",
    "wither",
    "anvil",
    "fallingBlock",
    "dragonBreath",
    "fireworks",
    "mob",
    "player",
    "arrow",
    "fireball",
    "thrown",
    "indirectMagic",
    "thorns",
    "explosion.player",
    "other"
]

ObservationFromDamageNumericKeys = {
    "damage_amount" : (0, 20),
    "damage_type_enum" : (0, len(DAMAGE_TYPE_KEYS)),
    "hunger_damage" : (0, 20), # How much food is consumed by this DamageSource
    "is_damage_absolute" : (0, 1), # Whether or not the damage ignores modification by potion effects or enchantments.
    "is_fire_damage" : (0, 1), # Whether the damage is fire based.
    "is_magic_damage" : (0, 1), # Whether the damage is magic based.
    "is_difficulty_scaled" : (0, 1), # Whether this damage source will have its damage amount scaled based on the current difficulty.
    "is_explosion" : (0, 1), # Whether the damage is from an explosion.
    "is_projectile" : (0, 1), # Returns true if the damage is projectile based.
    "is_unblockable" : (0, 1), # This kind of damage can be blocked or not.
    "death_message" : (0, 1),
    "damage_entity" : (0, 1),
    "damage_entity_registry_id" : (0, 120),
    "damage_pitch" : (-math.pi, math.pi),
    "damage_yaw" : (-math.pi, math.pi),
    "damage_relative_distance" : (0, 64),
}

ObservationFromDamageNonNumericKeys = [
    "damage_type",
    "death_message",
    "damage_entity",
    "damage_entity_uuid",
    "damage_location"
]

class ObservationFromDamageSource(TranslationHandlerGroup):

    def to_string(self) -> str:
        return "damage_source"

    def __init__(self):
        numeric_handlers = [_NumericObservationFromDamageSource(keys=[key], low=value[0], high=value[1])
                                for key, value in ObservationFromDamageNumericKeys.items()]
        # non_numeric_handlers = [_NonNumericObservationFromDamageSource(keys=key)
        #                         for key in ObservationFromDamageNonNumericKeys]
        super(ObservationFromDamageSource, self).__init__(handlers=numeric_handlers)

    def xml_template(self) -> str:
        return str("""<ObservationFromDamageSource/>""")

class _ObservationFromDamageSource(KeymapTranslationHandler):
    def __init__(self, keys, space, default_if_missing):
        keys = ["damage_source"] + keys
        super().__init__(hero_keys=keys, univ_keys=keys, space=space, default_if_missing=default_if_missing)
        self.dtype = space.dtype

    def to_hero(self, x) -> str:
        pass

    def from_hero(self, hero_dict):
        super(KeymapTranslationHandler).from_hero(hero_dict, dtype=self.dtype)

    def to_string(self) -> str:
        return "damage_source"

    def xml_template(self) -> str:
        return str("""<ObservationFromDamageSource/>""")

class _NumericObservationFromDamageSource(_ObservationFromDamageSource):
    def __init__(self, keys, low, high, default_if_missing=0):
        space = spaces.Box(low=low, high=high, shape=(), dtype=np.float)
        self.dtype = space.dtype
        super().__init__(keys=keys, space=space, default_if_missing=default_if_missing)


class _NonNumericObservationFromDamageSource(_ObservationFromDamageSource):
    def __init__(self, keys, default_if_missing=""):
        space = spaces.Text(shape=())
        super(_ObservationFromDamageSource).__init__(keys=keys, space=space, default_if_missing=default_if_missing)


