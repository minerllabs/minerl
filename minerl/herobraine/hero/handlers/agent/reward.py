
from minerl.herobraine.hero.handler import Handler
import jinja2
from typing import List,Dict,Union

# <RewardForPossessingItem sparse="true">
    # <Item amount="1" reward="1" type="log" />
    # <Item amount="1" reward="2" type="planks" />
# <RewardForPossessingItem sparse="true">

class RewardForPosessingItem(Handler):
    def to_string(self) -> str:
        return "reward_for_posessing_item"

    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<RewardForPossessingItem sparse="{{ str(sparse).lower() }}" excludeLoops="{{ str(exclude_loops).lower()}}">
                    {% for item in items %}
                    <Item amount="{{ item.amount }}" reward="{{ item.reward }}" type="{{ item.type }}" />
                    {% endfor %}
                </RewardForPossessingItem>
                """
        )

    def __init__(self, sparse : bool,  exclude_loops : bool, item_rewards : List[Dict[str, Union[str,int]]], ):
        """Creates a reward which gives rewards based on items in the 
        inventory that are provided.

        See Malmo for documentation.
        """
        self.sparse = sparse
        self.exclude_loops = exclude_loops
        self.items = item_rewards
        # Assert all items have the appropriate fields for the XML template.
        for item in self.items:
            assert set(item.keys()) == {"amount", "reward", "type"}


# <RewardForMissionEnd>
#     <Reward description="out_of_time" reward="0" />
# </RewardForMissionEnd>
class RewardForMissionEnd(Handler):
    def to_string(self) -> str:
        return "reward_for_mission_end"

    def xml_element(self) -> jinja2.Template:
        return jinja2.Template(
            """<RewardForMissionEnd>
                    <Reward description="{{ description }}" reward="{{ reward }}" />
                </RewardForMissionEnd>"""
        )
    
    def __init__(self, reward : int, description :str = "out_of_time"):
        """Creates a reward which is awarded when a mission ends."""
        self.reward = reward
        self.description = description


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
