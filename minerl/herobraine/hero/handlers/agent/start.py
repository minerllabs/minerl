# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

"""Defines the agent start conditions"""
from minerl.herobraine.hero.handler import Handler
from typing import Dict, List, Union

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


class AgentStartPlacement(Handler):
    def to_string(self) -> str:
        return f"agent_start_placement({self.x}, {self.y}, {self.z}, {self.yaw})"

    def xml_template(self) -> str:
        return str(
            """<Placement x="{{x}}" y="{{y}}" z="{{z}}" yaw="{{yaw}}" />"""
        )

    def __init__(self, x, y, z, yaw):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw


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
