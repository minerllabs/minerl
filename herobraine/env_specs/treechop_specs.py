from typing import List

import herobraine
import herobraine.hero.handlers as handlers
from herobraine.env_specs.env_spec import EnvSpec

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

class Treechop(SimpleEnvSpec):
    def __init__(self):
        super().__init__(
            name='MineRLTreechop-v0', xml='treechop.xml',
            max_episode_steps=8000, reward_threshold=64.0)

    def is_from_folder(folder: str) -> bool:
        return folder == 'survivaltreechop'

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.EpisodeLength(self.episode_len),
            handlers.RewardForCollectingItems(
                {"log": 1.0}
            )
        ]

    def get_docstring(self):
        return TREECHOP_DOC