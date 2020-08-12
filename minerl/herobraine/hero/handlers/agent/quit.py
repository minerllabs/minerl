from minerl.herobraine.hero.handler import Handler
import jinja2
from typing import List, Dict, Union


#  <AgentQuitFromTouchingBlockType>
#     <Block type="diamond_block"/>
#     <Block type="iron_block"/>
# </AgentQuitFromTouchingBlockType>
class AgentQuitFromTouchingBlock(Handler):
    def to_string(self) -> str:
        return "agent_quit_from_touching_block"
    
    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<AgentQuitFromTouchingBlock>
                    {% for block in blocks %}
                    <Block type="{{ block }}"/>
                    {% endfor %}
                </AgentQuitFromTouchingBlock>"""
        )

    def __init__(self, blocks: List[str]):
        """Creates a reward which will cause the player to quit when they touch a block."""
        self.blocks = blocks


# <AgentQuitFromCraftingItem>
#     <Item type="iron_pickaxe"/>
#     <Item type="wooden_axe"/>
#     <Item type="chest"/>
# </AgentQuitFromCraftingItem>
class  AgentQuitFromCraftingItem(Handler):
    def to_string(self) -> str:
        return "agent_quit_from_crafting_item"
    
    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<AgentQuitFromCraftingItem>
                    {% for item in items %}
                    <Item type="{{ item.type }}"/>
                    {% endfor %}
                </AgentQuitFromCraftingItem>"""
        )

    def __init__(self, items : List[Dict[str, Union[str, int]]]):
        """Creates a reward which will cause the player to quit when they have finished crafting something."""
        self.items = items
        # Assert that all the items have the correct fields for the XML.
        for item in self.items:
            assert "type" in item, "{} does not contain `type`".format(item)
            

#  <AgentQuitFromPossessingItem>
#     <Item type="log" amount="64"/>
# </AgentQuitFromPossessingItem>
class AgentQuitFromPossessingItem(Handler):
    def to_string(self) -> str:
        return "agent_quit_from_possessing_item"
    
    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
             """<AgentQuitFromPossessingItem>
                    {% for item in items %}
                    <Item type="{{ item.type }}" amount="{{ item.amount }}"/>
                    {% endfor %}
                </AgentQuitFromPossessingItem>"""
        )

    def __init__(self, items : List[Dict[str, Union[str, int]]]):
        """Creates a reward which will cause the player to quit when they obtain something.
        
        aqfpi = AgentQuitFromPossessingItem([
            dict(type="log", amount=64)
        ])
        """
        assert isinstance(items, list)
        self.items = items
        # Assert that all the items have the correct fields for the XML.
        for item in self.items:
            print(item)
            assert "type" in item, "{} does contain `type`".format(item)
            assert "amount" in item, "{} does not contain `amount`".format(item)

