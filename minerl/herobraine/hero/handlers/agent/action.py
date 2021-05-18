# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import collections
import typing
from abc import ABC
from typing import Any, Dict, Optional, Set, Sequence, Tuple

import numpy as np
from minerl.herobraine.hero import spaces
from minerl.herobraine.hero.handlers.translation import TranslationHandler

from collections import Iterable


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
        elif isinstance(x, Iterable) and not isinstance(x, str):
            adjective = " ".join([str(y) for y in x])
        else:
            adjective = str(x)
        cmd += "{} {}".format(verb, adjective)

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
    def __init__(self, command: str, items: list, _default='none', _other='other'):
        """
        Initializes the space of the handler with a gym.spaces.Dict
        of all of the spaces for each individual command.
        """
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

    def from_hero(self, x: typing.Dict[str, Any]):
        pass

    def xml_template(self) -> str:
        pass

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


def decode_item_maybe_with_metadata(s: str) -> Tuple[str, Optional[int]]:
    assert len(s) > 0
    if '#' in s:
        item_type, metadata_str = s.split('#')
        assert len(item_type) > 0
        if metadata_str == '?':
            return item_type, None
        else:
            metadata = int(metadata_str)
            assert metadata in range(16)
            return item_type, int(metadata_str)
    return s, None


def encode_item_with_metadata(item_type: str, metadata: Optional[int]) -> str:
    assert len(item_type) > 0
    if metadata is None:
        return f"{item_type}#?"
    else:
        return f"{item_type}#{metadata}"


def error_on_malformed_item_list(items: Sequence[str], special_items: Sequence[str]):
    map_type_to_metadata: Dict[str, Set[Optional[int]]] = collections.defaultdict(set)
    for s in items:
        item_type, metadata = decode_item_maybe_with_metadata(s)
        if item_type in special_items and metadata is not None:
            raise ValueError(
                f"Non-None metadata={metadata} is not allowed for special item type '{item_type}'")

        metadata_set = map_type_to_metadata[item_type]
        if metadata in metadata_set:
            raise ValueError(f"Duplicate item entry for item '{s}'")
        map_type_to_metadata[item_type].add(metadata)

    for item_type, metadata_set in map_type_to_metadata.items():
        if None in metadata_set and len(metadata_set) != 1:
            raise ValueError(
                f"Item list overlaps for item_type={item_type}. This item list includes "
                "both the wildcard metadata option and at least one specific metadata: "
                f"{[n for n in metadata_set if n is not None]}"
            )


class ItemWithMetadataListAction(ItemListAction, ABC):
    """
    Overrides ItemListAction.to_hero() to process item parameters with metadata.

    Validates item list to confirm that items are non-overlapping.
    """

    def __init__(self, command, items, **kwargs):
        super().__init__(command, items, **kwargs)
        error_on_malformed_item_list(items, [self._other, self._default, "air"])

    def to_hero(self, x):
        assert isinstance(x, str)
        # Validate item type and metadata, and appends #? if necessary.
        item_type, metadata = decode_item_maybe_with_metadata(x)
        return super().to_hero(encode_item_with_metadata(item_type, metadata))
