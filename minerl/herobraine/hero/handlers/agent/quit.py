
#  <RewardForTouchingBlockType>
#     <Block reward="100.0" type="diamond_block" behaviour="onceOnly"/>
#     <Block reward="189.0" type="diamond_block" behaviour="onceOnly"/>
# </RewardForTouchingBlockType>
class RewardForTouchingBlockType(Handler):
    def to_string(self) -> str:
        return "reward_for_touching_block_type"

    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<RewardForTouchingBlockType>
                    {% for block in blocks %}
                    <Block reward="{{ block.reward }}" type="{{ block.type }}" behaviour="{{ block.behaviour }}" />
                    {% endfor %}
                </RewardForTouchingBlockType>"""
        )

    def __init__(self, blocks : List[Dict[str, Union[str, int]]]):
        """Creates a reward which is awarded when the player touches a block."""
        self.blocks = blocks
        # Assert all blocks have the appropriate fields for the XML template.
        for block in self.blocks:
            assert set(block.keys()) == {"reward", "type", "behaviour"}


# <RewardForDistanceTraveledToCompassTarget rewardPerBlock="1" density="PER_TICK"/>
class RewardForDistanceTraveledToCompassTarget(Handler):
    def to_string(self) -> str:
        return "reward_for_distance_traveled_to_compass_target"

    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<RewardForDistanceTraveledToCompassTarget rewardPerBlock="{{ rewardPerBlock }}" density="{{ density }}"/>"""
        )

    def __init__(self, reward_per_block : int, density : str):
        """Creates a reward which is awarded when the player reaches a certain distance from a target."""
        self.reward_per_block = reward_per_block
        self.density = density


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


# <AgentQuitFromPossessingItem>
    # <Item type="diamond" amount="2"/>
    # <Item type="wodden_pickaxe" amount="27"/>
    # <Item type="rock" amount="1"/>
# </AgentQuitFromPossessingItem>
class AgentQuitFromTouchingBlock(Handler):
    def to_string(self) -> str:
        return "agent_quit_from_touching_item"

    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<AgentQuitFromPossessingItem>
                    {% for item in items %}
                    <Item type="{{ item.type }}" amount="{{ item.amount }}"/>
                    {% endfor %}
                </AgentQuFromPossessingItem>"""
        )

    def __init__(self, items : List[Dict[str, Union[str, int]]]):
        """Creates a reward which will cause the player to quit when they are in a chest."""
        self.items = items
        # Assert that all the items have the correct fields for the XML.
        for item in self.items:
            assert "amount" in item, "{} does not contain `amount`".format(item)
            assert "type" in item, "{} does not contain `type`".format(item)
        

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
            
