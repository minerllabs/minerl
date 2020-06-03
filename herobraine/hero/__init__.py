"""
herobraine.hero -- The interface between Hero (Malmo) and the Herobraine package.
"""

import logging

logger = logging.getLogger(__name__)

import herobraine.hero.mc
import herobraine.hero.spaces

# from herobraine.hero.instance_manager import InstanceManager
from herobraine.hero.agent_handler import AgentHandler
# from herobraine.hero.env import HeroEnv
from herobraine.hero.mc import KEYMAP
