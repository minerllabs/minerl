# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

from minerl.herobraine.hero.handler import Handler
import jinja2
from typing import List, Dict, Union


#  <AgentQuitFromTouchingBlockType>
#     <Block type="diamond_block"/>
#     <Block type="iron_block"/>
# </AgentQuitFromTouchingBlockType>
class AgentQuitFromTouchingBlockType(Handler):
    def to_string(self) -> str:
        return "agent_quit_from_touching_block_type"

    def xml_template(self) -> str:
        return str(
            """<AgentQuitFromTouchingBlockType>
                    {% for block in blocks %}
                    <Block type="{{ block }}"/>
                    {% endfor %}
                </AgentQuitFromTouchingBlockType>"""
        )

    def __init__(self, blocks: List[str]):
        """Creates a reward which will cause the player to quit when they touch a block."""
        self.blocks = blocks


# <AgentQuitFromCraftingItem>
#     <Item type="iron_pickaxe"/>
#     <Item type="wooden_axe"/>
#     <Item type="chest"/>
# </AgentQuitFromCraftingItem>
class AgentQuitFromCraftingItem(Handler):
    def to_string(self) -> str:
        return "agent_quit_from_crafting_item"

    def xml_template(self) -> str:
        return str(
            """<AgentQuitFromCraftingItem>
                    {% for item in items %}
                    <Item type="{{ item.type}}" amount="{{ item.amount }}"/>
                    {% endfor %}
                </AgentQuitFromCraftingItem>"""
        )

    def __init__(self, items: List[Dict[str, Union[str, int]]]):
        """Creates a reward which will cause the player to quit when they have finished crafting something."""
        self.items = items

        for item in self.items:
            assert "type" in item, "{} does contain `type`".format(item)
            assert "amount" in item, "{} does not contain `amount`".format(item)


#  <AgentQuitFromPossessingItem>
#     <Item type="log" amount="64"/>
# </AgentQuitFromPossessingItem>
class AgentQuitFromPossessingItem(Handler):
    def to_string(self) -> str:
        return "agent_quit_from_possessing_item"

    def xml_template(self) -> str:
        return str(
            """<AgentQuitFromPossessingItem>
                   {% for item in items %}
                   <Item type="{{ item.type }}" amount="{{ item.amount }}"/>
                   {% endfor %}
               </AgentQuitFromPossessingItem>"""
        )

    def __init__(self, items: List[Dict[str, Union[str, int]]]):
        """Creates a reward which will cause the player to quit when they obtain something.
        
        aqfpi = AgentQuitFromPossessingItem([
            dict(type="log", amount=64)
        ])
        """
        assert isinstance(items, list)
        self.items = items
        # Assert that all the items have the correct fields for the XML.
        for item in self.items:
            assert "type" in item, "{} does contain `type`".format(item)
            assert "amount" in item, "{} does not contain `amount`".format(item)
