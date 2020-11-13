# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import jinja2
from typing import List

from minerl.herobraine.hero.handlers.translation import KeymapTranslationHandler, TranslationHandlerGroup
import minerl.herobraine.hero.mc as mc
from minerl.herobraine.hero import spaces
import numpy as np

__all__ = ['ObserveFromFullStats']


class ObserveFromFullStats(TranslationHandlerGroup):
    """
    Includes the use_item statistics for every item in MC that can be used
    """

    def xml_template(self) -> str:
        return str("""<ObservationFromFullStats/>""")

    def to_string(self) -> str:
        return self.stat_key

    def __init__(self, stat_key):
        if stat_key is None:
            self.stat_key = "full_stats"
            super(ObserveFromFullStats, self).__init__(
                handlers=[_FullStatsObservation(statKeys) for statKeys in mc.ALL_STAT_KEYS if len(statKeys) == 2]
            )
        else:
            self.stat_key = stat_key
            super(ObserveFromFullStats, self).__init__(
                handlers=[_FullStatsObservation(statKeys) for statKeys in mc.ALL_STAT_KEYS if statKeys[1] == stat_key]
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
