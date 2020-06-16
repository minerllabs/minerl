import sys
from typing import List

import minerl.herobraine
import minerl.herobraine.hero.handlers as handlers
from minerl.herobraine.env_specs.simple_env_spec import SimpleEnvSpec


class Navigate(SimpleEnvSpec):
    def __init__(self, dense, extreme):
        suffix = 'Extreme' if extreme else ''
        suffix += 'Dense' if dense else ''
        name = 'MineRLNavigate{}-v0'.format(suffix)
        xml = 'navigation{}.xml'.format(suffix)
        self.dense, self.extreme = dense, extreme
        super().__init__(name, xml, max_episode_steps=6000)

    def is_from_folder(self, folder: str) -> bool:
        return folder == 'navigateextreme' if self.extreme else folder == 'navigate'

    def create_mission_handlers(self) -> List[minerl.herobraine.hero.AgentHandler]:
        mission_handlers = [
            handlers.EpisodeLength(6000 // 20),
            handlers.RewardForTouchingBlock(
                {"diamond_block", 100.0}
            ),
            handlers.NavigateTargetReward(),
            handlers.NavigationDecorator(
                min_radius=64,
                max_radius=64,
                randomize_compass_target=True
            )
        ]
        if self.dense:
            mission_handlers.append(handlers.RewardForWalkingTwardsTarget(
                reward_per_block=1, reward_schedule="PER_TICK"
            ))
        return mission_handlers

    def determine_success_from_rewards(self, rewards: list) -> bool:
        reward_threshold = 100.0
        if self.dense:
            reward_threshold += 60
        return sum(rewards) >= reward_threshold

    def create_observables(self) -> List[minerl.herobraine.hero.AgentHandler]:
        return super().create_observables() + [
            handlers.CompassObservation(),
            handlers.FlatInventoryObservation(['dirt'])]

    def create_actionables(self) -> List[minerl.herobraine.hero.AgentHandler]:
        return super().create_actionables() + [handlers.PlaceBlock(['none', 'dirt'])]

    def get_docstring(self):
        return make_navigate_text(
            top="normal" if not self.extreme else "extreme",
            dense=self.dense)


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

    if top is "normal":
        navigate_text += "\nIn this environment, the agent spawns on a random survival map.\n"
        navigate_text = navigate_text.format(*["" for _ in range(4)])
    else:
        navigate_text += "\nIn this environment, the agent spawns in an extreme hills biome.\n"
        navigate_text = navigate_text.format(*["extreme" for _ in range(4)])
    return navigate_text
