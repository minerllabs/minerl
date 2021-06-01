"""
    Defines observations on whether nearby crafting and smelting is possible.
"""
from collections import defaultdict
import jinja2
import numpy as np

from minerl.herobraine.hero import spaces

from minerl.herobraine.hero.handlers.translation import (
    KeymapTranslationHandler,
    TranslationHandlerGroup,
)
from minerl.herobraine.hero.mc import UNBREAKABLE_BLOCKS


__all__ = ["ObservationCanCraft"]


class ObservationCanCraft(TranslationHandlerGroup):
    """Groups all of the observations relevant to being able to craft."""

    def to_string(self) -> str:
        return "can_craft"

    def __init__(self):
        # TODO: nearby crafting table and furnace should be somewhere else.
        super(ObservationCanCraft, self).__init__(handlers=[_NearbyCraftingTableObservation(), _NearbyFurnaceObservation()])

    def xml_template(self) -> str:
        # We don't include anything in the XML template because the relevant observation comes from the NearbyCraft and NearbySmelt
        # commands, and we want them to be enabled as commands rather than observations.
        return ""


class _NearbyCraftingTableObservation(KeymapTranslationHandler):
    def __init__(self):
        keys = ["nearby_crafting_table"]
        super().__init__(
            hero_keys=keys,
            univ_keys=keys,
            space=spaces.Box(low=0, high=1, shape=(), dtype=np.int),
            default_if_missing=1,
        )

    def to_string(self) -> str:
        return "nearby_crafting_table"

    def from_hero(self, info):
        return int(info.get("nearby_crafting_table", 1))

class _NearbyFurnaceObservation(KeymapTranslationHandler):
    def __init__(self):
        keys = ["nearby_furnace"]
        super().__init__(
            hero_keys=keys,
            univ_keys=keys,
            space=spaces.Box(low=0, high=1, shape=(), dtype=np.int),
            default_if_missing=1,
        )

    def to_string(self) -> str:
        return "nearby_furnace"

    def from_hero(self, info):
        return int(info.get("nearby_furnace", 1))