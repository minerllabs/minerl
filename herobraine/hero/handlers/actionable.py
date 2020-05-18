from abc import ABC

import gym
import numpy as np
from gym import spaces

from herobraine.hero import AgentHandler
from herobraine.hero import KEYMAP
from herobraine.hero.spaces import DiscreteRange


from minerl.env import spaces as minerl_spaces


class CommandAction(AgentHandler):
    """
    An action handler based on commands
    # Todo: support blacklisting commands.
    """

    def __init__(self, command: str, space: gym.Space):
        """
        Initializes the space of the handler with a gym.spaces.Dict
        of all of the spaces for each individual command.
        """
        self._command = command
        super().__init__(space)

    @property
    def command(self):
        return self._command

    def to_hero(self, x):
        """
        Returns a command string for the multi command action.
        :param x:
        :return:
        """
        cmd = ""
        verb = self.command

        if isinstance(x, np.ndarray):
            flat = x.flatten().tolist()
            flat = [str(y) for y in flat]
            adjective = " ".join(flat)
        elif isinstance(x, list):
            adjective = " ".join([str(y) for y in x])
        else:
            adjective = str(x)
        cmd += "{} {}".format(
            verb, adjective)

        return cmd


class ItemListCommandAction(CommandAction):
    """
    An action handler based on a list of items
    The action space is determiend by the length of the list plus one
    """

    def __init__(self, command: str, items: list):
        """
        Initializes the space of the handler with a gym.spaces.Dict
        of all of the spaces for each individual command.
        """

        # TODO must check that the first element is 'none' and last elem is 'other'
        self._command = command
        self._items = items
        self._univ_items = ['minecraft:' + item for item in items]
        self._default = 0  # 'none'
        super().__init__(self._command, minerl_spaces.Enum(*self._items))

    @property
    def items(self):
        return self._items

    @property
    def universal_items(self):
        return self._univ_items

    @property
    def default(self):
        return self._default

    def to_hero(self, x):
        """
        Returns a command string for the multi command action.
        :param x:
        :return:
        """
        cmd = ""
        verb = self._command

        if isinstance(x, np.ndarray):
            raise NotImplementedError
        elif isinstance(x, list):
            raise NotImplementedError
        elif 0 < x < len(self._items):
            adjective = self._items[x]
            cmd += "{} {}".format(
                verb, adjective)
        else:
            cmd += "{} NONE".format(
                verb)

        return cmd


class CraftItem(ItemListCommandAction):
    """
    An action handler for crafting items

        Note when used along side Craft Item Nearby, block lists must be disjoint or from_universal will fire multiple
        times

    """
    _command = "craft"

    @staticmethod
    def to_string():
        return "craft"

    def __init__(self, items: list):
        """
        Initializes the space of the handler to be one for each item in the list plus one for the
        default no-craft action (command 0)

        Items are minecraft resource ID's
        """
        super().__init__(self._command, items)

    def from_universal(self, obs):
        if 'diff' in obs and 'crafted' in obs['diff'] and len(obs['diff']['crafted']) > 0:
            try:
                return self._univ_items.index(obs['diff']['crafted'][0]['item'])
            except ValueError:
                return self._default
                # return self._items.index('other')
        else:
            return self._default


class CraftItemNearby(CraftItem):
    """
    An action handler for crafting items when agent is in view of a crafting table

        Note when used along side Craft Item, item lists must be disjoint or from_universal will fire multiple times

    """
    _command = "craftNearby"

    @staticmethod
    def to_string():
        return 'nearbyCraft'


class SmeltItem(CraftItem):
    def from_universal(self, obs):
        if 'diff' in obs and 'smelted' in obs['diff'] and len(obs['diff']['smelted']) > 0:
            try:
                return self._univ_items.index(obs['diff']['smelted'][0]['item'])
            except ValueError:
                return self._default
                # return self._items.index('other')
        else:
            return self._default

class SmeltItemNearby(SmeltItem):
    """
    An action handler for crafting items when agent is in view of a crafting table

        Note when used along side Craft Item, block lists must be disjoint or from_universal will fire multiple times

    """
    _command = 'smeltNearby'

    @staticmethod
    def to_string():
        return 'nearbySmelt'


class PlaceBlock(ItemListCommandAction):
    """
    An action handler for placing a specific block
    """

    @staticmethod
    def to_string():
        return 'place'

    def __init__(self, blocks: list):
        """
        Initializes the space of the handler to be one for each item in the list
        Requires 0th item to be 'none' and last item to be 'other' coresponding to
        no-op and non-listed item respectively
        """
        self._items = blocks
        self._command = 'place'
        super().__init__(self._command, self._items)
        self._prev_inv = None
        # print(self._items)
        # print(self._univ_items)

    def from_universal(self, obs):
        try:
            for action in obs['custom_action']['actions'].keys():
                try:
                    if int(action) == -99 and self._prev_inv is not None:
                        return self._univ_items.index(self._prev_inv[int(-10 + obs['hotbar'])]['name'])
                except ValueError:
                    return self._default
        except TypeError:
            print('Saw a type error in PlaceBlock')
            raise TypeError
        except KeyError:
            return self._default
        finally:
            try:
                self._prev_inv = obs['slots']['gui']['slots']
            except KeyError:
                self._prev_inv = None

        return self._default


class EquipItem(ItemListCommandAction):
    """
    An action handler for placing a specific block
    """

    @staticmethod
    def to_string():
        return 'equip'

    def __init__(self, items: list):
        """
        Initializes the space of the handler to be one for each item in the list plus one for the
        default no-craft action
        """
        self._items = items
        self._command = 'equip'
        super().__init__(self._command, self._items)
        self.previous = self._default
        # print(self._items)
        # print(self._univ_items)

    def from_universal(self, obs):
        try:
            if obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerPlayer':
                hotbar_index = int(obs['hotbar'])
                item = self._univ_items.index(obs['slots']['gui']['slots'][-10 + hotbar_index]['name'])
                if item != self.previous:
                    self.previous = item
                    return item
        except KeyError:
            return self._default
        except ValueError:
            return self._default
            # return self._items.index('other')
        return self._default

    def reset(self):
        self.previous = self._default


class ContinuousMovementAction(CommandAction, ABC):
    """
    Handles player control actions
    """

    def add_to_mission_spec(self, mission_spec):
        mission_spec.allowAllContinuousMovementCommands()
        pass


class KeyboardAction(ContinuousMovementAction):
    """
    Handles keyboard actions.

    """

    def to_string(self):
        return self.command

    def __init__(self, command, keys):
        if len(keys) == 2:
            # Like move or strafe. Example: -1 for left, 1 for right
            super().__init__(command, DiscreteRange(-1, 2))
        else:
            # Its a n-key action with discrete items.
            # Eg hotbar actions
            super().__init__(command, spaces.Discrete(len(keys)+1))
        self.keys = keys

    def from_universal(self, x):
        actions_mapped = []
        for action in x['custom_action']['actions'].keys():
            try:
                actions_mapped += [KEYMAP[action]]
            except KeyError:
                pass

        offset = self.space.begin if isinstance(self.space, DiscreteRange) else 0
        default = 0
        for i, key in enumerate(self.keys):
            if key in actions_mapped:
                if isinstance(self.space, DiscreteRange):
                    return i*2 + offset
                else:
                    return i + 1 + offset

        # if "BUTTON1" in actions_mapped:
        #     print("BUTTON1")
        # If no key waspressed.
        return default

class SingleKeyboardAction(ContinuousMovementAction):
        """
        Handles keyboard actions.
        """

        def to_string(self):
            return self.command

        def __init__(self, command, key):
            super().__init__(command, spaces.Discrete(2))
            self.key = key

        def from_universal(self, x):
            if 'custom_action' in x and 'actions' in x['custom_action']:
                if self.key in x['custom_action']['actions'].keys():
                    return 1
                else:
                    return 0


class MouseAction(ContinuousMovementAction):
    """
    The same as a keyboard action except it captures
    """

    def __init__(self, command, key):
        self._command = command
        self.key = key
        super().__init__(command, spaces.Box(-1,1, [1]))

    def from_universal(self, x):
        if self.key in x['custom_action']:

            assert not np.isnan(np.sum(x['custom_action'][self.key])), "NAN in action!"
            return ([x['custom_action'][self.key] / 360])
        else:
            return np.array([0.0]).tolist()


class Camera(ContinuousMovementAction):
    """
    Uses <delta_pitch, delta_yaw> vector in degrees to rotate the camera. pitch range [-180, 180], yaw range [-180, 180]
    """

    @staticmethod
    def to_string():
        return 'camera'

    def __init__(self):
        self._command = 'camera'
        super().__init__(self.command, spaces.Box(low=-180, high=180, shape=[2], dtype=np.float32))

    def from_universal(self, x):
        if 'custom_action' in x and 'cameraYaw' in x['custom_action'] and 'cameraPitch' in x['custom_action']:
            delta_pitch = x['custom_action']['cameraPitch']
            delta_yaw = x['custom_action']['cameraYaw']
            assert not np.isnan(np.sum(x['custom_action']['cameraYaw'])), "NAN in action!"
            assert not np.isnan(np.sum(x['custom_action']['cameraPitch'])), "NAN in action!"
            return np.array([-delta_pitch, -delta_yaw], dtype=np.float32)
        else:
            return np.array([0.0, 0.0], dtype=np.float32)


class DiscreteMouseAction(ContinuousMovementAction):
    """
    The same as a keyboard action except it captures
    """

    def __init__(self, command, key):
        self._command = command
        self.key = key
        super().__init__(command, DiscreteRange(-1,2))

    def from_universal(self, x):
        if self.key in x['custom_action']:
            # assert not np.isnan(np.sum(x['custom_action'][self.key])), "NAN in action!"
            val = ([x['custom_action'][self.key]])
            out = int(np.sign(val))
            assert out in [-1,0,1]
            return out

        else:
            return 0
