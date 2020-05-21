import abc


from herobraine.hero import handlers
from herobraine.hero.mc import INVERSE_KEYMAP
from herobraine.env_specs.env_spec import EnvSpec

from typing import List

class SimpleEnvSpec(EnvSpec, abc.ABC):
    """
    A simple base environment from which all othe simple envs inherit.
    """
    STANDARD_KEYBOARD_ACTIONS = [
        "forward",
        "back",
        "left",
        "right",
        "jump",
        "sneak",
        "sprint"
        "attack"
    ]
    
    def __init__(self, name, xml, *args, **kwargs):
        self.resolution = tuple((64, 64))
        super().__init__(name, xml, *args, **kwargs)
    
    def create_observables(self) -> List[herobraine.hero.AgentHandler]:
        return [
            handlers.POVObservation(self.resolution)
        ]

    def create_actionables(self) -> List[herobraine.hero.AgentHandler]:
        """
        Simple envs have some basic keyboard control functionality, but
        not all.
        """
        return  [
            handlers.KeyboardAction(k, v) for k,v in INVERSE_KEYMAP.items()
            if k in SimpleEnvSpec.STANDARD_KEYBOARD_ACTIONS
        ] + [
            handlers.Camera()
        ]

# Place_handler = [
#     w, A, S, D
# ] 
# Place_handler = [
#     W, A
# ] 

# act1 = [
#     handlers.KeyboardAction("move", "S", "W"),
#     handlers.CraftItem([
#         'planks',
#         'stick',
#         'torch']),
# ]


# ac2 = [
#     handlers.KeyboardAction("move", "S", "W"), -
#     handlers.KeyboardAction("attack", "BUTTON0"),
#     handlers.KeyboardAction("use", "BUTTON1"),
#     handlers.CraftItem([
#         'planks',
#         'torch']),
# ]

# # Step 1. 
# # h.to_string() <-> malmo
# {
#     handlers.KeyboardAction: [
#         handlers.KeyboardAction("move", "S", "W"),
#         handlers.KeyboardAction("move", "S", "W"),
#         handlers.KeyboardAction("attack", "BUTTON0"),
#         handlers.KeyboardAction("use", "BUTTON1"),
#         ]
# }



# {
#     "move": [
#         handlers.KeyboardAction("move", "S", "W"),
#         handlers.KeyboardAction("move", "S", "W"),],
#     "attack": [
#         handlers.KeyboardAction("attack", "BUTTON0"),
#     ],
#     "use": sum([
#         handlers.KeyboardAction("hotbar", "1", "2", "3"),
#         handlers.KeyboardAction("hotbar", "1", "2", "3", "4", "5"),
#     ])
# }
