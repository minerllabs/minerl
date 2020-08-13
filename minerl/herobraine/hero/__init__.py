# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

"""
minerl.herobraine.hero -- The interface between Hero (Malmo) and the minerl.herobraine package.
"""

import logging

logger = logging.getLogger(__name__)

import minerl.herobraine.hero.mc
import minerl.herobraine.hero.spaces

from minerl.herobraine.hero.mc import KEYMAP
