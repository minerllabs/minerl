from typing import List

import herobraine
import herobraine.hero.handlers as handlers
from herobraine.task import Task


class ObtainIronPickaxe(Task):
    def __init__(self, name, resolution, episode_length, ms_per_tick, no_pitch=False):
        self.resolution = tuple(resolution)
        self.ms_per_tick = ms_per_tick
        self.episode_len = episode_length
        self.no_pitch = no_pitch
        super().__init__(name)


    def get_filter(self, source):
        pass

    def get_mission_file(self) -> str:
        return "./obtain_iron_pickaxe.xml"

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.TickHandler(self.ms_per_tick),
            handlers.EpisodeLength(self.episode_len),
            handlers.RewardForCollectingItemsDict({
                "log" : 1,
                "planks" : 2,
                "stick" : 4,
                "crafting_table" : 4,
                "wooden_pickaxe" : 8,
                "stone" : 16,
                "furnace" : 32,
                "stone_pickaxe" : 32,
                "iron_ore" : 64,
                "iron_ingot" : 128,
                "iron_pickaxe" : 256})
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
            # handlers.KeyboardAction("move", "S", "W"),
            # handlers.KeyboardAction("strafe", "A", "D"),
            # handlers.KeyboardAction("jump", "SPACE"),
            # handlers.KeyboardAction("crouch", "SHIFT"),
            # handlers.KeyboardAction("attack", "BUTTON0"),
            # handlers.KeyboardAction("use", "BUTTON1"),
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
        # if not self.no_pitch:
        #     actionables += [handlers.MouseAction("pitch", "cameraPitch")]
        # actionables += [handlers.MouseAction("turn", "cameraYaw")]
        return actionables