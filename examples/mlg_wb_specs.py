"""MLG Water Bucket Gym"""

__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from minerl.herobraine.env_specs.simple_embodiment import SimpleEmbodimentEnvSpec
from minerl.herobraine.hero.handler import Handler
import minerl.herobraine.hero.handlers as handlers
from typing import List

MLGWB_DOC = """
In MLG Water Bucket, an agent must perform an "MLG Water Bucket" jump onto a gold block. 
Then the agent mines the block to terminate the episode.
See the Custom Environments Tutorial for more information on this environment.
"""

MLGWB_LENGTH = 8000

class MLGWB(SimpleEmbodimentEnvSpec):
    def __init__(self, *args, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = 'MLGWB-v0'

        super().__init__(*args,
                        max_episode_steps=MLGWB_LENGTH, reward_threshold=100.0,
                        **kwargs)

    def create_server_world_generators(self) -> List[Handler]:
        return [
            handlers.FlatWorldGenerator(generatorString="1;7,2x3,2;1"),
            # generate a 3x3 square of obsidian high in the air and a gold block
            # somewhere below it on the ground
            handlers.DrawingDecorator("""
                <DrawCuboid x1="0" y1="5" z1="-6" x2="0" y2="5" z2="-6" type="gold_block"/>
                <DrawCuboid x1="-2" y1="88" z1="-2" x2="2" y2="88" z2="2" type="obsidian"/>
            """)
        ]

    def create_agent_start(self) -> List[Handler]:
        return [
            # make the agent start with these items
            handlers.SimpleInventoryAgentStart([
                dict(type="water_bucket", quantity=1), 
                dict(type="diamond_pickaxe", quantity=1)
            ]),
            # make the agent start 90 blocks high in the air
            handlers.AgentStartPlacement(0, 90, 0, 0, 0)
        ]

    def create_rewardables(self) -> List[Handler]:
        return [
            # reward the agent for touching a gold block (but only once)
            handlers.RewardForTouchingBlockType([
                {'type':'gold_block', 'behaviour':'onceOnly', 'reward':'50'},
            ]),
            # also reward on mission end
            handlers.RewardForMissionEnd(50)
        ]

    def create_agent_handlers(self) -> List[Handler]:
        return [
            # make the agent quit when it gets a gold block in its inventory
            handlers.AgentQuitFromPossessingItem([
                dict(type="gold_block", amount=1)
            ])
        ]
    
    def create_actionables(self) -> List[Handler]:
        return super().create_actionables() + [
            # allow agent to place water
            handlers.KeybasedCommandAction("use"),
            # also allow it to equip the pickaxe
            handlers.EquipAction(["diamond_pickaxe"])
        ]

    def create_observables(self) -> List[Handler]:
        return super().create_observables() + [
            # current location and lifestats are returned as additional
            # observations
            handlers.ObservationFromCurrentLocation(),
            handlers.ObservationFromLifeStats()
        ]
    
    def create_server_initial_conditions(self) -> List[Handler]:
        return [
            # Sets time to morning and stops passing of time
            handlers.TimeInitialCondition(False, 23000)
        ]

    def create_server_quit_producers(self):
        return []
    
    def create_server_decorators(self) -> List[Handler]:
        return []

    # the episode can terminate when this is True
    def determine_success_from_rewards(self, rewards: list) -> bool:
        return sum(rewards) >= self.reward_threshold

    def is_from_folder(self, folder: str) -> bool:
        return folder == 'mlgwb'

    def get_docstring(self):
        return MLGWB_DOC