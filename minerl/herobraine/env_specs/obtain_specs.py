import gym

from minerl.env import _fake, _singleagent
from minerl.herobraine.env_specs.human_survival_specs import HumanSurvival
from minerl.herobraine.hero.handlers.translation import TranslationHandler
from minerl.herobraine.hero.handler import Handler
from minerl.herobraine.hero import handlers
from minerl.herobraine.hero.mc import ALL_ITEMS
from typing import List

TIMEOUT = 18000
DIAMOND_ITEMS = [
    [["acacia_log", "birch_log", "dark_oak_log", "jungle_log", "oak_log", "spruce_log"], 1],
    [["acacia_planks", "birch_planks", "dark_oak_planks", "jungle_planks", "oak_planks", "spruce_planks"], 2],
    [["stick"], 4],
    [["crafting_table"], 4],
    [["wooden_pickaxe"], 8],
    [["cobblestone"], 16],
    [["furnace"], 32],
    [["stone_pickaxe"], 32],
    [["iron_ore"], 64],
    [["iron_ingot"], 128],
    [["iron_pickaxe"], 256],
    [["diamond"], 1024],
    [["diamond_shovel"], 2048]
]


class ObtainDiamondShovelWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.rewarded_items = DIAMOND_ITEMS
        self.seen = [0] * len(self.rewarded_items)
        self.timeout = self.env.task.max_episode_steps
        self.num_steps = 0
        self.episode_over = False

    def step(self, action: dict):
        if self.episode_over:
            raise RuntimeError("Expected `reset` after episode terminated, not `step`.")
        observation, reward, done, info = super().step(action)
        for i, [item_list, rew] in enumerate(self.rewarded_items):
            if not self.seen[i]:
                for item in item_list:
                    if observation["inventory"][item] > 0:
                        if i == len(self.rewarded_items) - 1:  # achieved last item in rewarded item list
                            done = True
                        reward += rew
                        self.seen[i] = 1
                        break
        self.num_steps += 1
        if self.num_steps >= self.timeout:
            done = True
        self.episode_over = done
        return observation, reward, done, info

    def reset(self):
        self.seen = [0] * len(self.rewarded_items)
        self.episode_over = False
        obs = super().reset()
        return obs


def _obtain_diamond_shovel_gym_entrypoint(env_spec, fake=False):
    """Used as entrypoint for `gym.make`."""
    if fake:
        env = _fake._FakeSingleAgentEnv(env_spec=env_spec)
    else:
        env = _singleagent._SingleAgentEnv(env_spec=env_spec)

    env = ObtainDiamondShovelWrapper(env)
    return env

OBTAIN_DIAMOND_SHOVEL_ENTRY_POINT = "minerl.herobraine.env_specs.obtain_specs:_obtain_diamond_shovel_gym_entrypoint"

class ObtainDiamondShovelEnvSpec(HumanSurvival):
    r"""
In this environment the agent is required to obtain a diamond shovel.
The agent begins in a random starting location on a random survival map
without any items, matching the normal starting conditions for human players in Minecraft.

During an episode the agent is rewarded according to the requisite item
hierarchy needed to obtain a diamond shovel. The rewards for each item are
given here::

    <Item reward="1" type="log" />
    <Item reward="2" type="planks" />
    <Item reward="4" type="stick" />
    <Item reward="4" type="crafting_table" />
    <Item reward="8" type="wooden_pickaxe" />
    <Item reward="16" type="cobblestone" />
    <Item reward="32" type="furnace" />
    <Item reward="32" type="stone_pickaxe" />
    <Item reward="64" type="iron_ore" />
    <Item reward="128" type="iron_ingot" />
    <Item reward="256" type="iron_pickaxe" />
    <Item reward="1024" type="diamond" />
    <Item reward="2048" type="diamond_shovel" />
"""
    def __init__(self):
        super().__init__(
            name="MineRLObtainDiamondShovel-v0",
            max_episode_steps=TIMEOUT,
            # Hardcoded variables to match the pretrained models
            fov_range=[70, 70],
            resolution=[640, 360],
            gamma_range=[2, 2],
            guiscale_range=[1, 1],
            cursor_size_range=[16.0, 16.0]
        )

    def _entry_point(self, fake: bool) -> str:
        return OBTAIN_DIAMOND_SHOVEL_ENTRY_POINT

    def create_observables(self) -> List[Handler]:
        return [
            handlers.POVObservation(self.resolution),
            handlers.FlatInventoryObservation(ALL_ITEMS)
        ]

    def create_monitors(self) -> List[TranslationHandler]:
        return []


