from minerl.herobraine.env_specs.human_controls import HumanControlEnvSpec
from minerl.herobraine.hero.mc import MS_PER_STEP, STEPS_PER_MS, ALL_ITEMS
from minerl.herobraine.hero.handler import Handler
import minerl.herobraine.hero.handlers as handlers
from typing import List

import minerl.herobraine
import minerl.herobraine.hero.handlers as handlers
from minerl.herobraine.env_spec import EnvSpec

EPISODE_LENGTH = 1200
WEAPON = "iron_axe"


class EquipWeapon(HumanControlEnvSpec):
    def __init__(self, hotbar=True, *args, **kwargs):
        self.hotbar = hotbar
        if "name" not in kwargs:
            kwargs["name"] = "MineRLEquipWeapon-v0"

        super().__init__(
            *args, max_episode_steps=EPISODE_LENGTH, reward_threshold=64.0, **kwargs
        )

    def create_rewardables(self) -> List[Handler]:
        return [
            # handlers.RewardForPickingItemInInventory([dict(type=WEAPON, reward=1.0)])
            # handlers.RewardForEquippingItem([dict(type=WEAPON, reward=5.0)])
        ]

    def create_agent_start(self) -> List[Handler]:
        return super().create_agent_start() + \
             [handlers.RandomInventoryAgentStart({WEAPON: 1}, use_hotbar=self.hotbar)]

    def create_observables(self) -> List[Handler]:
        return super().create_observables() + [
            handlers.EquippedItemObservation(
                items=ALL_ITEMS, mainhand=True, _default="air", _other="air"
            ),
        ]

    def create_agent_handlers(self) -> List[Handler]:
        return [
            # handlers.AgentQuitFromEquippingItem([
            #     dict(type=WEAPON)]
            # )
        ]

    def create_server_world_generators(self) -> List[Handler]:
        return [handlers.DefaultWorldGenerator(force_reset=True)]

    def create_server_quit_producers(self) -> List[Handler]:
        return [
            handlers.ServerQuitFromTimeUp((EPISODE_LENGTH * MS_PER_STEP)),
            handlers.ServerQuitWhenAnyAgentFinishes(),
        ]

    def create_server_decorators(self) -> List[Handler]:
        return []

    def create_server_initial_conditions(self) -> List[Handler]:
        return [
            handlers.TimeInitialCondition(allow_passage_of_time=False),
            handlers.SpawningInitialCondition(allow_spawning=True),
        ]

    def determine_success_from_rewards(self, rewards: list) -> bool:
        return sum(rewards) >= self.reward_threshold

    def is_from_folder(self, folder: str) -> bool:
        return False

    def get_docstring(self):
        return ""
