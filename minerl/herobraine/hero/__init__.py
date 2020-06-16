"""
minerl.herobraine.hero -- The interface between Hero (Malmo) and the minerl.herobraine package.
"""

import logging

logger = logging.getLogger(__name__)

import minerl.herobraine.hero.mc
import minerl.herobraine.hero.spaces

# from minerl.herobraine.hero.instance_manager import InstanceManager
from minerl.herobraine.hero.agent_handler import AgentHandler
# from minerl.herobraine.hero.env import HeroEnv
from minerl.herobraine.hero.mc import KEYMAP
