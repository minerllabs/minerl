from minerl.env import spaces
from minerl.core.mc import ALL_ITEMS

ALL_WORDS = set([i for item in ALL_ITEMS for i in item.split('_')])

ITEMS_SPACE = spaces.Enum(*ALL_ITEMS)

class Buttons():
    ATTACK = "attack"
    BACK = "back"
    FORWARD = "forward"
    JUMP = "jump"
    LEFT = "left"
    RIGHT = "right"
    SNEAK = "sneak"
    SPRINT = "sprint"
    USE = "use"

    ALL = [ATTACK, BACK, FORWARD, JUMP, LEFT, RIGHT, SNEAK, SPRINT, USE]