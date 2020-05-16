from typing import List

import herobraine
import herobraine.hero.handlers as handlers
from herobraine.env_specs.env_spec import EnvSpec


class ObtainIronPickaxe(EnvSpec):
    def __init__(self, name='MineRLObtainIronPickaxe-v0'):
        self.resolution = tuple((64, 64))
        self.episode_len = 400
        super().__init__(name, self.resolution)

    @staticmethod
    def is_from_folder(folder: str) -> bool:
        return folder == 'o_iron'

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.EpisodeLength(self.episode_len),
            handlers.RewardForCollectingItemsOnce({
                "log": 1,
                "planks": 2,
                "stick": 4,
                "crafting_table": 4,
                "wooden_pickaxe": 8,
                "cobblestone": 16,
                "furnace": 32,
                "stone_pickaxe": 32,
                "iron_ore": 64,
                "iron_ingot": 128,
                "iron_pickaxe": 256})
        ]

    def create_observables(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.POVObservation(self.resolution),
            handlers.FlatInventoryObservation([
                'wooden_axe',
                'stone_axe',
                'coal',
                'torch',
                'log',
                'planks',
                'stick',
                'crafting_table',
                'wooden_pickaxe',
                'stone_pickaxe',
                'furnace',
                'iron_ore',
                'iron_ingot',
                'iron_pickaxe'
            ])
        ]

    def create_actionables(self) -> List[herobraine.hero.AgentHandler]:
        actionables = [
            handlers.KeyboardAction("move", "S", "W"),
            handlers.KeyboardAction("strafe", "A", "D"),
            handlers.KeyboardAction("jump", "SPACE"),
            handlers.KeyboardAction("crouch", "SHIFT"),
            handlers.KeyboardAction("attack", "BUTTON0"),
            handlers.KeyboardAction("use", "BUTTON1"),
            handlers.CraftItem([
                'planks',
                'stick',
                'torch']),
            handlers.CraftItemNearby([
                'wooden_pickaxe',
                'stone_pickaxe',
                'iron_pickaxe',
                'wooden_axe',
                'stone_axe',
                'furnace',
                'crafting_table']),
            handlers.SmeltItemNearby([
                'iron_ingot',
                'coal']),
            handlers.PlaceBlock([
                'crafting_table',
                'furnace',
                'torch'])
        ]
        actionables += [handlers.MouseAction("pitch", "cameraPitch")]
        actionables += [handlers.MouseAction("turn", "cameraYaw")]
        return actionables

class ObtainIronPickaxeDense(EnvSpec):
    def __init__(self, name='MineRLObtainIronPickaxeDense-v0'):
        self.resolution = tuple((64, 64))
        self.episode_len = 400
        super().__init__(name, self.resolution)

    @staticmethod
    def is_from_folder(folder: str) -> bool:
        return folder == 'o_iron'

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.EpisodeLength(self.episode_len),
            handlers.RewardForCollectingItems({
                "log": 1,
                "planks": 2,
                "stick": 4,
                "crafting_table": 4,
                "wooden_pickaxe": 8,
                "cobblestone": 16,
                "furnace": 32,
                "stone_pickaxe": 32,
                "iron_ore": 64,
                "iron_ingot": 128,
                "iron_pickaxe": 256})
        ]

    def create_observables(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.POVObservation(self.resolution),
            handlers.FlatInventoryObservation([
                'wooden_axe',
                'stone_axe',
                'coal',
                'torch',
                'log',
                'planks',
                'stick',
                'crafting_table',
                'wooden_pickaxe',
                'stone_pickaxe',
                'furnace',
                'iron_ore',
                'iron_ingot',
                'iron_pickaxe'
            ])
        ]

    def create_actionables(self) -> List[herobraine.hero.AgentHandler]:
        actionables = [
            handlers.KeyboardAction("move", "S", "W"),
            handlers.KeyboardAction("strafe", "A", "D"),
            handlers.KeyboardAction("jump", "SPACE"),
            handlers.KeyboardAction("crouch", "SHIFT"),
            handlers.KeyboardAction("attack", "BUTTON0"),
            handlers.KeyboardAction("use", "BUTTON1"),
            handlers.CraftItem([
                'planks',
                'stick',
                'torch']),
            handlers.CraftItemNearby([
                'wooden_pickaxe',
                'stone_pickaxe',
                'iron_pickaxe',
                'wooden_axe',
                'stone_axe',
                'furnace',
                'crafting_table']),
            handlers.SmeltItemNearby([
                'iron_ingot',
                'coal']),
            handlers.PlaceBlock([
                'crafting_table',
                'furnace',
                'torch'])
        ]
        actionables += [handlers.MouseAction("pitch", "cameraPitch")]
        actionables += [handlers.MouseAction("turn", "cameraYaw")]
        return actionables
