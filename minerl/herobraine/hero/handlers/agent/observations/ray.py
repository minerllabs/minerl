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
from minerl.herobraine.hero.mc import UNBREAKABLE_BLOCKS


__all__ = ["ObservationFromRay"]


class ObservationFromRay(TranslationHandlerGroup):
    """Groups all of the lifestats observations together to correspond to one XML element.."""

    def to_string(self) -> str:
        return "ray_obs"

    def __init__(self):
        super(ObservationFromRay, self).__init__(handlers=[_BlockPseudoIdObservation()])

    def xml_template(self) -> str:
        return str("""<ObservationFromRay/>""")


class _BlockPseudoIdObservation(KeymapTranslationHandler):
    def __init__(self):
        """

        The block pseudo-id is -1 when the agent is not looking at a block, and increments each
        time the agent looks at a different block than the timestep before. For instance, if
        the agent is looking at block A, the pseudo-id might be 0. If it moves to block B, the
        pseudo-id will be 1. If it moves back to block A, the pseudo-id will be 2 (NOT 0).

        """
        keys = ["block_pseudo_id"]
        super().__init__(
            hero_keys=keys,
            univ_keys=keys,
            space=spaces.Box(low=-1, high=spaces.MAX_INT, shape=(), dtype=np.int),
            default_if_missing=-1,
        )
        self.cur_block = defaultdict(lambda: None)
        self.cur_id = defaultdict(int)

    def to_string(self) -> str:
        return "block_pseudo_id"

    def from_hero(self, info):
        agent_name = info["name"]
        # This means there is no object in front of the agent (e.g. looking at the sky)
        if "LineOfSight" not in info:
            self.cur_block[agent_name] = None
            return -1
        los = info["LineOfSight"]
        if (
            los["hitType"] == "block"
            and los["inRange"]
            and los["type"] not in UNBREAKABLE_BLOCKS
        ):
            block_desc = (
                int(los["x"]),
                int(los["y"]),
                int(los["z"]),
                los["type"],
                los.get("variant"),
            )
            self.cur_id[agent_name] += block_desc != self.cur_block[agent_name]
            self.cur_block[agent_name] = block_desc
            return self.cur_id[agent_name]
        else:
            self.cur_block[agent_name] = None
            return -1
