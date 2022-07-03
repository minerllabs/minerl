# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

"""Defines the agent start conditions"""
from minerl.herobraine.hero.handler import Handler
from typing import Dict, List, Union
import random

import jinja2


# <AgentStart>
#     <Inventory>
#         <InventoryObject slot="0" type="dirt"/>
#         <InventoryObject slot="1" type="planks" quantity="3"/>
#         <InventoryObject slot="2" type="log2" quantity="2"/>
#         <InventoryObject slot="3" type="log" quantity="3"/>
#         <InventoryObject slot="4" type="iron_ore" quantity="4"/>
#         <InventoryObject slot="5" type="diamond_ore" quantity="2"/>
#         <InventoryObject slot="6" type="cobblestone" quantity="17"/>
#         <InventoryObject slot="7" type="red_flower" quantity="1"/>
#         ...
#     </Inventory>
# </AgentStart>
class InventoryAgentStart(Handler):
    def to_string(self) -> str:
        return "inventory_agent_start"

    def xml_template(self) -> str:
        return str(
            """<Inventory>
            {% for  slot in inventory %}
                <InventoryObject slot="{{ slot }}" type="{{ inventory[slot]['type'] }}" quantity="{{ inventory[slot]['quantity'] }}"/>
            {% endfor %}
            </Inventory>
            """
        )

    def __init__(self, inventory: Dict[int, Dict[str, Union[str, int]]]):
        """Creates an inventory agent start which sets the inventory of the
        agent by slot id.

        For example:

            ias = InventoryAgentStart(
            {
                0: {'type':'dirt', 'quantity':10},
                1: {'type':'planks', 'quantity':5},
                5: {'type':'log', 'quantity':1},
                6: {'type':'log', 'quantity':2},
                32: {'type':'iron_ore', 'quantity':4}
            )

        Args:
            inventory (Dict[int, Dict[str, Union[str,int]]]): The inventory slot description.
        """
        self.inventory = inventory


class SimpleInventoryAgentStart(InventoryAgentStart):
    """ An inventory agentstart specification which
    just fills the inventory of the agent sequentially.
    """
    def __init__(self, inventory : List[Dict[str, Union[str, int]]]):
        """ Creates a simple inventory agent start.

        For example:

            sias =  SimpleInventoryAgentStart(
                [
                    {'type':'dirt', 'quantity':10},
                    {'type':'planks', 'quantity':5},
                    {'type':'log', 'quantity':1},
                    {'type':'iron_ore', 'quantity':4}
                ]
            )
        """
        super().__init__({
            i: item for i, item in enumerate(inventory)
        })


class RandomInventoryAgentStart(InventoryAgentStart):
    """ An inventory agentstart specification which
    that fills
    """
    def __init__(self, inventory: Dict[str, Union[str, int]], use_hotbar: bool = False):
        """ Creates an inventory where items are placed in random positions

        For example:

            rias =  RandomInventoryAgentStart({'dirt': 10, 'planks': 5})
        """
        self.inventory = inventory
        self.slot_range = (0, 36) if use_hotbar else (10, 36)

    def xml_template(self) -> str:
        lines = ['<Inventory>']
        for item, quantity in self.inventory.items():
            slot = random.randint(*self.slot_range)
            lines.append(f'<InventoryObject slot="{slot}" type="{item}" quantity="{quantity}"/>')
        lines.append('</Inventory>')
        return '\n'.join(lines)


class AgentStartBreakSpeedMultiplier(Handler):
    def to_string(self) -> str:
        return f"agent_start_break_speed_multiplier({self.multiplier})"

    def xml_template(self) -> str:
        return str(
            """<BreakSpeedMultiplier>{{multiplier}}</BreakSpeedMultiplier>"""
        )

    def __init__(self, multiplier=1.0):
        self.multiplier = multiplier


class AgentStartPlacement(Handler):
    def to_string(self) -> str:
        return f"agent_start_placement({self.x}, {self.y}, {self.z}, {self.yaw}, {self.pitch})"

    def xml_template(self) -> str:
        return str(
            """<Placement x="{{x}}" y="{{y}}" z="{{z}}" yaw="{{yaw}}" pitch="{{pitch}}"/>"""
        )

    def __init__(self, x, y, z, yaw=0.0, pitch=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch

class AgentStartVelocity(Handler):
    def to_string(self) -> str:
        return f"agent_start_velocity({self.x}, {self.y}, {self.z})"

    def xml_template(self) -> str:
        return str(
            """<Velocity x="{{x}}" y="{{y}}" z="{{z}}"/>"""
        )

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class AgentStartNear(Handler):
    def to_string(self) -> str:
        return f"agent_start_near({self.anchor_name}, h {self.min_distance} - {self.max_distance}, v {self.max_vert_distance})"

    def xml_template(self) -> str:
        return str(
            """<NearPlayer>
                    <Name>{{anchor_name}}</Name>
                    <MaxDistance>{{max_distance}}</MaxDistance>
                    <MinDistance>{{min_distance}}</MinDistance>
                    <MaxVertDistance>{{max_vert_distance}}</MaxVertDistance>
                    <LookingAt>true</LookingAt>
               </NearPlayer>""")

    def __init__(self, anchor_name="MineRLAgent0", min_distance=2, max_distance=10, max_vert_distance=3):
        self.anchor_name = anchor_name
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.max_vert_distance = max_vert_distance


class StartingHealthAgentStart(Handler):
    def to_string(self) -> str:
        return "starting_health_agent_start"

    def xml_template(self) -> str:
        if self.health is None:
            return str(
                """<StartingHealth maxHealth="{{ max_health }}"/>"""
            )
        else:
            return str(
                """<StartingHealth maxHealth="{{ max_health }}" health="{{ health }}"/>"""
            )

    def __init__(self, max_health: float = 20, health: float = None):
        """Sets the starting health of the agent.

        For example:

            starting_health = StartingHealthAgentStart(2.5)

        Args:
            max_health: The maximum amount of health the agent can have
            health: The amount of health the agent starts with (max_health if not specified)
        """
        self.health = health
        self.max_health = max_health


class StartingFoodAgentStart(Handler):
    def to_string(self) -> str:
        return "starting_food_agent_start"

    def xml_template(self) -> str:
        if self.food_saturation is None:
            return str(
                """<StartingFood food="{{ food }}"/>"""
            )
        else:
            return str(
                """<StartingHealth food="{{ food }}" foodSaturation="{{ food_saturation }}"/>"""
            )

    def __init__(self, food: int = 20, food_saturation: float = None):
        """Sets the starting food of the agent.

        For example:

            starting_health = StartingFoodAgentStart(2.5)

        Args:
            food: The amount of food the agent starts out with
            food_saturation: The food saturation the agent starts out with (if not specified, set to max)
        """
        self.food = food
        self.food_saturation = food_saturation


class LowLevelInputsAgentStart(Handler):
    def to_string(self) -> str:
        return "low_level_inputs"

    def xml_template(self) -> str:
        return "<LowLevelInputs>true</LowLevelInputs>"

class GuiScale(Handler):
    def __init__(self, gui_scale=2):
        self.gui_scale = gui_scale

    def to_string(self) -> str:
        return "gui_scale"

    def xml_template(self) -> str:
        return "<GuiScale>{{gui_scale}}</GuiScale>"


class GammaSetting(Handler):
    def __init__(self, gamma_setting=2.0):
        self.gamma_setting = gamma_setting

    def to_string(self) -> str:
        return "gamma_setting"

    def xml_template(self) -> str:
        return "<GammaSetting>{{gamma_setting}}</GammaSetting>"


class FOVSetting(Handler):
    def __init__(self, fov_setting=130.0):
        self.fov_setting = fov_setting

    def to_string(self) -> str:
        return "fov_setting"

    def xml_template(self) -> str:
        return "<FOVSetting>{{fov_setting}}</FOVSetting>"

class FakeCursorSize(Handler):
    def __init__(self, size=16):
        self.size = size

    def to_string(self) -> str:
        return "fake_cursor_size"

    def xml_template(self) -> str:
        return "<FakeCursorSize>{{size}}</FakeCursorSize>"

class LoadWorldAgentStart(Handler):
    def __init__(self, filename):
        self.filename = filename

    def to_string(self) -> str:
        return "load_world_file"

    def xml_template(self) -> str:
        _filename = None
        if callable(self.filename):
            _filename = self.filename()
        elif isinstance(self.filename, str):
            _filename = self.filename
        if _filename is not None:
            return f"<LoadWorldFile>{_filename}</LoadWorldFile>"
        return ""

class PreferredSpawnBiome(Handler):
    def __init__(self, biome):
        self.biome = biome
    def to_string(self):
        return "preferred_spawn_biome"
    def xml_template(self) -> str:
        _biome = None
        if callable(self.biome):
            _biome = self.biome()
        elif isinstance(self.biome, str):
            _biome = self.biome
        if _biome is not None:
            return f"<PreferredSpawnBiome>{_biome}</PreferredSpawnBiome>"
        return ""

class EnableRecorder(Handler):
    def to_string(self) -> str:
        return "enable_recorder"
    def xml_template(self) -> str:
        return "<EnableRecorder>true</EnableRecorder>"

class MultiplayerUsername(Handler):
    def __init__(self, name: str):
        self.name = name

    def to_string(self):
        return "multiplayer_username"

    def xml_template(self) -> str:
        return "<MultiplayerUsername>{{ name }}</MultiplayerUsername>"

class SpawnInVillage(Handler):
    def to_string(self):
        return "start_in_village"
    def xml_template(self) -> str:
        return "<SpawnInVillage>true</SpawnInVillage>"

class DoneOnDeath(Handler):
    """This should probably be in quit.py etc, but those are not implemented in Java side yet"""
    def to_string(self):
        return "done_on_death"
    def xml_template(self) -> str:
        return "<DoneOnDeath>true</DoneOnDeath>"