from typing import List

import minerl.herobraine
import minerl.herobraine.hero.handlers as handlers
from minerl.herobraine.env_spec import EnvSpec

import minerl.herobraine.env_specs.simple_env_spec as ses

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
In treechop, the agent must collect 64 `minercaft:log`. This replicates a common scenario in Minecraft, as logs are necessary to craft a large amount of items in the game, and are a key resource in Minecraft.

The agent begins in a forest biome (near many trees) with an iron axe for cutting trees. The agent is given +1 reward for obtaining each unit of wood, and the episode terminates once the agent obtains 64 units.
"""


class Treechop(ses.SimpleEnvSpec):
    def __init__(self):
        super().__init__(
            name='MineRLTreechop-v0', xml='treechop.xml',
            max_episode_steps=8000, reward_threshold=64.0)

    def is_from_folder(self, folder: str) -> bool:
        return folder == 'survivaltreechop'

    def create_mission_handlers(self) -> List[minerl.herobraine.hero.AgentHandler]:
        return [
            handlers.EpisodeLength(8000 // 20),
            handlers.RewardForCollectingItems(
                {"log": 1.0}
            )
        ]

    def determine_success_from_rewards(self, rewards: list) -> bool:
        return sum(rewards) >= self.reward_threshold

    def get_docstring(self):
        return TREECHOP_DOC
