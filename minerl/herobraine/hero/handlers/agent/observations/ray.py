"""
    Defines observations from ray.
"""
from collections import defaultdict
import jinja2
import numpy as np

from minerl.herobraine.hero import spaces

from minerl.herobraine.hero.handlers.translation import (
    KeymapTranslationHandler,
    TranslationHandlerGroup,
)

__all__ = ["ObservationFromRay"]


class ObservationFromRay(TranslationHandlerGroup):
    """Groups all of the lifestats observations together to correspond to one XML element.."""

    def to_string(self) -> str:
        return "ray_obs"

    def __init__(self):
        super(ObservationFromRay, self).__init__(handlers=[_BlockIdObservation()])

    def xml_template(self) -> str:
        return str("""<ObservationFromRay/>""")


class _BlockIdObservation(KeymapTranslationHandler):
    def __init__(self):
        keys = ["block_id"]
        super().__init__(
            hero_keys=keys,
            univ_keys=keys,
            space=spaces.Box(low=-1, high=np.inf, shape=(), dtype=np.int),
            default_if_missing=-1,
        )
        self.cur_block = defaultdict(lambda: None)
        self.cur_id = defaultdict(int)

    def to_string(self) -> str:
        return "block_id"

    def from_hero(self, info):
        name = info["name"]
        # This means there is no object in front of the agent (e.g. looking at the sky)
        if "LineOfSight" not in info:
            return -1
        los = info["LineOfSight"]
        if los["hitType"] == "block" and los["inRange"]:
            block_desc = (
                int(los["x"]),
                int(los["y"]),
                int(los["z"]),
                los["type"],
                los.get("variant"),
            )
            self.cur_id[name] += block_desc != self.cur_block[name]
            self.cur_block[name] = block_desc
            return self.cur_id[name]
        else:
            self.cur_block[name] = None
            return -1
