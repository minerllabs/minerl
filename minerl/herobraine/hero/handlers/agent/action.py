# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import typing
from typing import Any

import numpy as np
from minerl.herobraine.hero import spaces
from minerl.herobraine.hero.handlers.translation import TranslationHandler


class Action(TranslationHandler):
    """
    An action handler based on commands
    # Todo: support blacklisting commands. (note this has to work with mergeing somehow)
    """

    def __init__(self, command: str, space: spaces.MineRLSpace):
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
        elif hasattr(x, "__iter__") and not isinstance(x, str):
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


class ItemListAction(Action):
    """
    An action handler based on a list of items
    The action space is determined by the length of the list plus one
    """

    def from_hero(self, x: typing.Dict[str, Any]):
        pass

    def xml_template(self) -> str:
        pass

    def __init__(self, command: str, items: list, _default='none', _other='other'):
        """
        Initializes the space of the handler with a gym.spaces.Dict
        of all of the spaces for each individual command.
        """

        # TODO must check that the first element is 'none' and last elem is 'other'
        self._command = command
        self._items = items
        self._univ_items = ['minecraft:' + item for item in items]
        if _other not in self._items or _default not in self._items:
            print(self._items)
            print(_default)
            print(_other)
        assert _default in self._items
        assert _other in self._items
        self._default = _default
        self._other = _other
        super().__init__(
            self._command,
            spaces.Enum(*self._items, default=self._default))

    @property
    def items(self):
        return self._items

    @property
    def universal_items(self):
        return self._univ_items

    @property
    def default(self):
        return self._default

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
        return self.__class__(new_items, _default=self._default, _other=self._other)

    def __eq__(self, other):
        """
        Asserts equality between item list command actions.
        """
        if not isinstance(other, ItemListAction):
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
