# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

from minerl.herobraine.env_specs.simple_embodiment import SimpleEmbodimentEnvSpec
from minerl.herobraine.hero.mc import MS_PER_STEP, STEPS_PER_MS
from minerl.herobraine.hero.handler import Handler
from typing import List

import minerl.herobraine
import minerl.herobraine.hero.handlers as handlers
from minerl.herobraine.env_spec import EnvSpec

TREECHOP_DOC = """
.. image:: ../assets/treechop1.mp4.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/treechop2.mp4.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/treechop3.mp4.gif
  :scale: 100 %
  :alt:

.. image:: ../assets/treechop4.mp4.gif
  :scale: 100 %
  :alt:
In treechop, the agent must collect 64 `minecraft:log`. This replicates a common scenario
in Minecraft, as logs are necessary to craft a large amount of items in the game and are a
key resource in Minecraft.

The agent begins in a forest biome (near many trees) with an iron axe for cutting trees. The agent
is given +1 reward for obtaining each unit of wood, and the episode terminates once the agent
obtains 64 units.
"""
TREECHOP_LENGTH = 8000
TREECHOP_WORLD_GENERATOR_OPTIONS = '''{
    "coordinateScale": 684.412,
    "heightScale": 684.412,
    "lowerLimitScale": 512.0,
    "upperLimitScale": 512.0,
    "depthNoiseScaleX": 200.0,
    "depthNoiseScaleZ": 200.0,
    "depthNoiseScaleExponent": 0.5,
    "mainNoiseScaleX": 80.0,
    "mainNoiseScaleY": 160.0,
    "mainNoiseScaleZ": 80.0,
    "baseSize": 8.5,
    "stretchY": 12.0,
    "biomeDepthWeight": 1.0,
    "biomeDepthOffset": 0.0,
    "biomeScaleWeight": 1.0,
    "biomeScaleOffset": 0.0,
    "seaLevel": 1,
    "useCaves": false,
    "useDungeons": false,
    "dungeonChance": 8,
    "useStrongholds": false,
    "useVillages": false,
    "useMineShafts": false,
    "useTemples": false,
    "useMonuments": false,
    "useMansions": false,
    "useRavines": false,
    "useWaterLakes": false,
    "waterLakeChance": 4,
    "useLavaLakes": false,
    "lavaLakeChance": 80,
    "useLavaOceans": false,
    "fixedBiome": 4,
    "biomeSize": 4,
    "riverSize": 1,
    "dirtSize": 33,
    "dirtCount": 10,
    "dirtMinHeight": 0,
    "dirtMaxHeight": 256,
    "gravelSize": 33,
    "gravelCount": 8,
    "gravelMinHeight": 0,
    "gravelMaxHeight": 256,
    "graniteSize": 33,
    "graniteCount": 10,
    "graniteMinHeight": 0,
    "graniteMaxHeight": 80,
    "dioriteSize": 33,
    "dioriteCount": 10,
    "dioriteMinHeight": 0,
    "dioriteMaxHeight": 80,
    "andesiteSize": 33,
    "andesiteCount": 10,
    "andesiteMinHeight": 0,
    "andesiteMaxHeight": 80,
    "coalSize": 17,
    "coalCount": 20,
    "coalMinHeight": 0,
    "coalMaxHeight": 128,
    "ironSize": 9,
    "ironCount": 20,
    "ironMinHeight": 0,
    "ironMaxHeight": 64,
    "goldSize": 9,
    "goldCount": 2,
    "goldMinHeight": 0,
    "goldMaxHeight": 32,
    "redstoneSize": 8,
    "redstoneCount": 8,
    "redstoneMinHeight": 0,
    "redstoneMaxHeight": 16,
    "diamondSize": 8,
    "diamondCount": 1,
    "diamondMinHeight": 0,
    "diamondMaxHeight": 16,
    "lapisSize": 7,
    "lapisCount": 1,
    "lapisCenterHeight": 16,
    "lapisSpread": 16
}'''


class Treechop(SimpleEmbodimentEnvSpec):
    def __init__(self, *args, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = 'MineRLTreechop-v0'

        super().__init__(*args,
                         max_episode_steps=TREECHOP_LENGTH, reward_threshold=64.0,
                         **kwargs)

    def create_rewardables(self) -> List[Handler]:
        return [
            handlers.RewardForCollectingItems([
                dict(type="log", amount=1, reward=1.0),
            ])
        ]

    def create_agent_start(self) -> List[Handler]:
        return [
            handlers.SimpleInventoryAgentStart([
                dict(type="iron_axe", quantity=1)
            ])
        ]

    def create_agent_handlers(self) -> List[Handler]:
        return [
            handlers.AgentQuitFromPossessingItem([
                dict(type="log", amount=64)]
            )
        ]

    def create_server_world_generators(self) -> List[Handler]:
        return [
            handlers.DefaultWorldGenerator(force_reset="true",
                                           generator_options=TREECHOP_WORLD_GENERATOR_OPTIONS
                                           )
        ]

    def create_server_quit_producers(self) -> List[Handler]:
        return [
            handlers.ServerQuitFromTimeUp(
                (TREECHOP_LENGTH * MS_PER_STEP)),
            handlers.ServerQuitWhenAnyAgentFinishes()
        ]

    def create_server_decorators(self) -> List[Handler]:
        return []

    def create_server_initial_conditions(self) -> List[Handler]:
        return [
            handlers.TimeInitialCondition(
                allow_passage_of_time=False
            ),
            handlers.SpawningInitialCondition(
                allow_spawning=True
            )
        ]

    def determine_success_from_rewards(self, rewards: list) -> bool:
        return sum(rewards) >= self.reward_threshold

    def is_from_folder(self, folder: str) -> bool:
        return folder == 'survivaltreechop'

    def get_docstring(self):
        return TREECHOP_DOC
