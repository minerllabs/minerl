# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

from minerl.herobraine.hero.mc import MS_PER_STEP, STEPS_PER_MS
from minerl.herobraine.env_specs.simple_embodiment import SimpleEmbodimentEnvSpec
from minerl.herobraine.hero.handler import Handler
import sys
from typing import List

import minerl.herobraine
import minerl.herobraine.hero.handlers as handlers

NAVIGATE_STEPS = 6000


class Navigate(SimpleEmbodimentEnvSpec):

    def __init__(self, dense, extreme, *args, **kwargs):
        suffix = 'Extreme' if extreme else ''
        suffix += 'Dense' if dense else ''
        name = 'MineRLNavigate{}-v0'.format(suffix)
        self.dense, self.extreme = dense, extreme
        super().__init__(name, *args, max_episode_steps=6000, **kwargs)

    def is_from_folder(self, folder: str) -> bool:
        return folder == 'navigateextreme' if self.extreme else folder == 'navigate'

    def create_observables(self) -> List[Handler]:
        return super().create_observables() + [
            handlers.CompassObservation(angle=True, distance=False),
            handlers.FlatInventoryObservation(['dirt'])]

    def create_actionables(self) -> List[Handler]:
        return super().create_actionables() + [
            handlers.PlaceBlock(['none', 'dirt'],
                                _other='none', _default='none')]

    # john rl nyu microsfot van roy and ian osband

    def create_rewardables(self) -> List[Handler]:
        return [
                   handlers.RewardForTouchingBlockType([
                       {'type': 'diamond_block', 'behaviour': 'onceOnly',
                        'reward': 100.0},
                   ])
               ] + ([handlers.RewardForDistanceTraveledToCompassTarget(
            reward_per_block=1.0
        )] if self.dense else [])

    def create_agent_start(self) -> List[Handler]:
        return [
            handlers.SimpleInventoryAgentStart([
                dict(type='compass', quantity='1')
            ])
        ]

    def create_agent_handlers(self) -> List[Handler]:
        return [
            handlers.AgentQuitFromTouchingBlockType(
                ["diamond_block"]
            )
        ]

    def create_server_world_generators(self) -> List[Handler]:
        if self.extreme:
            return [
                handlers.BiomeGenerator(
                    biome=3,
                    force_reset=True
                )
            ]
        else:
            return [
                handlers.DefaultWorldGenerator(
                    force_reset=True
                )
            ]

    def create_server_quit_producers(self) -> List[Handler]:
        return [
            handlers.ServerQuitFromTimeUp(NAVIGATE_STEPS * MS_PER_STEP),
            handlers.ServerQuitWhenAnyAgentFinishes()
        ]

    def create_server_decorators(self) -> List[Handler]:
        return [handlers.NavigationDecorator(
            max_randomized_radius=64,
            min_randomized_radius=64,
            block='diamond_block',
            placement='surface',
            max_radius=8,
            min_radius=0,
            max_randomized_distance=8,
            min_randomized_distance=0,
            randomize_compass_location=True
        )]

    def create_server_initial_conditions(self) -> List[Handler]:
        return [
            handlers.TimeInitialCondition(
                allow_passage_of_time=False,
                start_time=6000
            ),
            handlers.WeatherInitialCondition('clear'),
            handlers.SpawningInitialCondition('false')
        ]

    def get_docstring(self):
        return make_navigate_text(
            top="normal" if not self.extreme else "extreme",
            dense=self.dense)

    def determine_success_from_rewards(self, rewards: list) -> bool:
        reward_threshold = 100.0
        if self.dense:
            reward_threshold += 60
        return sum(rewards) >= reward_threshold


def make_navigate_text(top, dense):
    navigate_text = """
.. image:: ../assets/navigate{}1.mp4.gif
    :scale: 100 %
    :alt: 

.. image:: ../assets/navigate{}2.mp4.gif
    :scale: 100 %
    :alt: 

.. image:: ../assets/navigate{}3.mp4.gif
    :scale: 100 %
    :alt: 

.. image:: ../assets/navigate{}4.mp4.gif
    :scale: 100 %
    :alt: 

In this task, the agent must move to a goal location denoted by a diamond block. This represents a basic primitive used in many tasks throughout Minecraft. In addition to standard observations, the agent has access to a “compass” observation, which points near the goal location, 64 meters from the start location. The goal has a small random horizontal offset from the compass location and may be slightly below surface level. On the goal location is a unique block, so the agent must find the final goal by searching based on local visual features.

The agent is given a sparse reward (+100 upon reaching the goal, at which point the episode terminates). """
    if dense:
        navigate_text += "**This variant of the environment is dense reward-shaped where the agent is given a reward every tick for how much closer (or negative reward for farther) the agent gets to the target.**\n"
    else:
        navigate_text += "**This variant of the environment is sparse.**\n"

    if top == "normal":
        navigate_text += "\nIn this environment, the agent spawns on a random survival map.\n"
        navigate_text = navigate_text.format(*["" for _ in range(4)])
    else:
        navigate_text += "\nIn this environment, the agent spawns in an extreme hills biome.\n"
        navigate_text = navigate_text.format(*["extreme" for _ in range(4)])
    return navigate_text
