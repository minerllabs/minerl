from abc import ABC, abstractmethod

import gym
import numpy as np

from minerl.herobraine.hero import AgentHandler
from minerl.herobraine.hero import KEYMAP
from minerl.herobraine.hero import spaces
from minerl.herobraine.hero.spaces import DiscreteRange


class CommandAction(AgentHandler):
    """
    An action handler based on commands
    # Todo: support blacklisting commands. (note this has to work with mergeing somehow)
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

    def to_string(self):
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

    def __or__(self, other):
        if not self.command == other.command:
            raise ValueError("Command must be the same between {} and {}".format(self.command, other.command))

        return self


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
        assert 'none' in self._items
        self._default = 'none'
        super().__init__(self._command, spaces.Enum(*self._items, default=self._default))

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

    def from_universal(self, x):
        raise NotImplementedError()

    def __or__(self, other):
        """
        Merges two ItemListCommandActions into one by unioning their items.
        Assert that the commands are the same.
        """

        if not isinstance(other, self.__class__):
            raise TypeError("other must be an instance of ItemListCommandAction")

        if self._command != other._command:
            raise ValueError("Command must be the same for merging")

        new_items = list(set(self._items) | set(other._items))
        return self.__class__(new_items)

    def __eq__(self, other):
        """
        Asserts equality betwen item list command actions.
        """
        if not isinstance(other, ItemListCommandAction):
            return False
        if self._command != other._command:
            return False

        # Check that all items are in self._items
        if not all(x in self._items for x in other._items):
            return False

        # Check that all items are in other._items
        if not all(x in other._items for x in self._items):
            return False

        return True


class CraftItem(ItemListCommandAction):
    """
    An action handler for crafting items

        Note when used along side Craft Item Nearby, block lists must be disjoint or from_universal will fire multiple
        times

    """
    _command = "craft"

    def to_string(self):
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
                x =  self._univ_items.index(obs['diff']['crafted'][0]['item'])
                return obs['diff']['crafted'][0]['item'].split('minecraft:')[-1]
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

    def to_string(self):
        return 'nearbyCraft'


class SmeltItem(CraftItem):
    def from_universal(self, obs):
        if 'diff' in obs and 'smelted' in obs['diff'] and len(obs['diff']['smelted']) > 0:
            try:
                x =  self._univ_items.index(obs['diff']['smelted'][0]['item'])
                return obs['diff']['smelted'][0]['item'].split('minecraft:')[-1]
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

    def to_string(self):
        return 'nearbySmelt'


class PlaceBlock(ItemListCommandAction):
    """
    An action handler for placing a specific block
    """

    def to_string(self):
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

                        item_name = self._prev_inv[int(-10 + obs['hotbar'])]['name'].split("minecraft:")[-1]
                        if item_name not in self._items:
                            raise ValueError()
                        else:
                            return item_name
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
    An action handler for observing a list of equipped items
    """

    def to_string(self):
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
                    return obs['slots']['gui']['slots'][-10 + hotbar_index]['name'].split('minecraft:')[-1]
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


class Camera(ContinuousMovementAction):
    """
    Uses <delta_pitch, delta_yaw> vector in degrees to rotate the camera. pitch range [-180, 180], yaw range [-180, 180]
    """

    def to_string(self):
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


class KeyboardAction(ContinuousMovementAction):
    """
    Handles keyboard actions.

    """

    def to_string(self):
        return self.command

    def __init__(self, command, *keys):
        if len(keys) == 2:
            # Like move or strafe. Example: -1 for left, 1 for right
            super().__init__(command, DiscreteRange(-1, 2))
        else:
            # Its a n-key action with discrete items.
            # Eg hotbar actions
            super().__init__(command, spaces.Discrete(len(keys) + 1))
        self.keys = keys

    def from_universal(self, x):
        actions_mapped = list(x['custom_action']['actions'].keys())
        # actions_mapped is just the raw key codes.

        # for action in x['custom_action']['actions'].keys():
        #     try:
        #         actions_mapped += [KEYMAP[action]]
        #     except KeyError:
        #         pass

        offset = self.space.begin if isinstance(self.space, DiscreteRange) else 0
        default = 0

        for i, key in enumerate(self.keys):
            if key in actions_mapped:
                if isinstance(self.space, DiscreteRange):
                    return i * 2 + offset
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

    def __or__(self, other):
        """
        Combines two keyboard actions into one by unioning their keys.
        """
        if not isinstance(other, KeyboardAction):
            raise TypeError("other must be an instance of KeyboardAction")

        new_keys = list(set(self.keys + other.keys))
        return KeyboardAction(self._command, new_keys)

    def __eq__(self, other):
        """
        Tests for equality between two keyboard actions.
        """
        if not isinstance(other, KeyboardAction):
            return False

        return self._command == other._command and self.keys == other.keys
