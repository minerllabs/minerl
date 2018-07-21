from action_object import Action
from keycode_dict import keycode_dict

# press the button
BINDINGS = { 
    'W':'move 1', 
    'A':'strafe -1', 
    'S':'move -1', 
    'D':'strafe 1', 
    ' ':'jump 1',
    "K": 'pitch 1', 
    'I': 'pitch -1', 
    "L": 'turn 1', 
    "J": 'turn -1', 
    "N": 'attack 1',
    "M": 'use 1',
    'Q': 'discardCurrentItem 1',
    "1": 'hotbar.1 1',
    "2": 'hotbar.2 1',
    "3": 'hotbar.3 1',
    "4": 'hotbar.4 1',
    "5": 'hotbar.5 1',
    "6": 'hotbar.6 1',
    "7": 'hotbar.7 1',
    "8": 'hotbar.8 1',
    "9": 'hotbar.9 1',
    "BUTTON0": 'attack 1',
    "BUTTON1": 'use 1',
    'LSHIFT': 'crouch 1'
    }


IGNORES = {'TAB'}
# defaults 
'''
    { 
    'w':'move 0', 
    'a':'strafe 0', 
    's':'move 0', 
    'd':'strafe 0', 
    ' ':'jump 0',
    "k": 'pitch 0', 
    'i': 'pitch 0', 
    "l": 'turn 0', 
    "j": 'turn 0', 
    "n": 'attack 0',
    "m": 'use 0'
    }
'''

# return string
def get_hotbar_index(action):
    assert(action.startswith("hotbar."))
    return action[7]


# first tick then actions
# only add actions to temp when have a tick

def parse_to_action_object(parse_result):
    keycode = keycode_dict()
    result = [] # return result
    temp = dict() # a temporary storage
    seen_tick = False
    first_tick = True
    hotbar_curr = set() # curr tick need to release hotbar
    hotbar_next = set() # next tick need to release hotbar

    for item in parse_result:
        # tick
        if type(item) is bool: 
            if item: # ignore tick = False
                seen_tick = True
                # do not add to action if this is the first tick
                # i.e. no actions before it
                if first_tick: 
                    first_tick = False
                else:
                    # release hotbars if necessary
                    for hotbar_index in hotbar_curr:
                        # release hotbar by adding to temp
                        temp["hotbar."+hotbar_index] = "0"

                    # set curr = next and reset next bc moving to next tick
                    hotbar_curr = hotbar_next
                    hotbar_next = set()

                    # add actions
                    a = Action(temp)
                    result.append(a)
                    # reset temp, seen_tick
                    temp = dict() 
            else:
                seen_tick = False
                    

        # keycode
        elif type(item) is int:
            # first check error, must already seen a tick 
            if not seen_tick: raise ValueError("detect actions without a tick")
            keyboard = keycode[item]
            if keyboard not in IGNORES and keyboard in BINDINGS:
                info = BINDINGS[keyboard].split(" ")
                action = info[0] # string (e.g. "move")
                value = info[1] # string (e.g. "1")
                temp[action] = value 
                # check for releasing hotbars
                if action.startswith("hotbar."):
                    i = get_hotbar_index(action) # i is a string
                    hotbar_curr.discard(i) 
                    hotbar_next.add(i)

        # pitch/yaw
        elif type(item) is str:
            # first check error, must already seen a tick 
            if not seen_tick: raise ValueError("detect actions without a tick")
            info = item.split(" ")
            action = info[0] # "pitch" or "turn"
            value = info[1] # float as string
            temp[action] = value

        else:
            raise ValueError("Unknown Type")
    return result


