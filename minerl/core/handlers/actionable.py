from abc import ABC

import gym
import numpy as np
from gym import spaces

from minerl.core.mc import KEYMAP
from minerl.core.spaces import DiscreteRange
from minerl.core.handlers.agent_handler import AgentHandler


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
    The action space is determined by the length of the list plus one
    """

    def __init__(self, command: str, items: list):
        """
        Initializes the space of the handler with a gym.spaces.Dict
        of all of the spaces for each individual command.
        """
        self._command = command
        self._items = items
        self._univ_items = ['minecraft:' + item for item in items]
        self._default = 0
        super().__init__(self._command, spaces.Discrete(len(self._items) + 1))

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
        elif 0 < x < len(self._items) + 1:
            adjective = self._items[x - 1]
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

    def __init__(self, items: list):
        """
        Initializes the space of the handler to be one for each item in the list plus one for the
        default no-craft action (command 0)

        Items are minecraft resource ID's
        """
        super().__init__(self._command, items)

    def from_universal(self, obs):
        if 'inventory' in obs and 'crafted' in obs['inventory'] and len(obs['inventory']['crafted']) > 0:
            try:
                return self._univ_items.index(obs['inventory']['crafted'][0]['item']) + 1
            except ValueError:
                return self._default
        else:
            return self._default


class CraftItemNearby(CraftItem):
    """
    An action handler for crafting items when agent is in view of a crafting table

        Note when used along side Craft Item, item lists must be disjoint or from_universal will fire multiple times

    """
    _command = "craftNearby"


class SmeltItem(CraftItem):
    def from_universal(self, obs):
        if 'inventory' in obs and 'smelted' in obs['inventory'] and len(obs['inventory']['smelted']) > 0:
            try:
                return self._univ_items.index(obs['inventory']['smelted'][0]['item']) + 1
            except ValueError:
                return self._default
        else:
            return self._default

class SmeltItemNearby(SmeltItem):
    """
    An action handler for crafting items when agent is in view of a crafting table

        Note when used along side Craft Item, block lists must be disjoint or from_universal will fire multiple times

    """
    _command = 'smeltNearby'


class PlaceBlock(ItemListCommandAction):
    """
    An action handler for placing a specific block
    """

    def __init__(self, blocks: list):
        """
        Initializes the space of the handler to be one for each item in the list plus one for the
        default no-craft action
        """
        self._items = blocks
        self._command = 'place'
        super().__init__(self._command, self._items)

    def from_universal(self, obs):
        if 'custom_action' in obs and 'actions' in obs['custom_action'] and len(obs['custom_action']['actions']) > 0:
            for action in obs['custom_action']['actions'].keys():
                if action == -99:
                    try:
                        return self._univ_items.index(obs['slots']['inventory'][obs['hotbar']]['item'])
                    except ValueError:
                        return self._default
        else:
            return self._default


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

    def __init__(self, command, *keys):
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
