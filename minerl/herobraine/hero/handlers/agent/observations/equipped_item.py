# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton


"""
"""
# Not very proud of the code reuse in this module -- @wguss

import os
from typing import List, Sequence

from minerl.herobraine.hero import mc
from minerl.herobraine.hero import spaces
from minerl.herobraine.hero.handlers import util
from minerl.herobraine.hero.handlers.translation import TranslationHandler, TranslationHandlerGroup
import numpy as np

__all__ = ['EquippedItemObservation']


class EquippedItemObservation(TranslationHandlerGroup):
    """
    Enables the observation of equipped items in the main, offhand,
    and armor slots of the agent.
    """

    def to_string(self) -> str:
        return "equipped_items"

    def xml_template(self) -> str:
        return str(
            """<ObservationFromEquippedItem/>""")

    def __init__(self,
                 items: Sequence[str],
                 mainhand: bool = True,
                 offhand: bool = False,
                 armor: bool = False,
                 _default: str = 'none',
                 _other: str = 'other'):
        self.mainhand = mainhand
        self.offhand = offhand
        self.armor = armor
        self._items = list(items)
        self._other = _other
        self._default = _default
        if self._other not in self._items:
            self._items.append(self._other)
        if self._default not in self._items:
            self._items.append(self._default)

        handlers = []
        if mainhand:
            handlers.append(
                _EquippedItemObservation(['mainhand'], self._items, _default=_default, _other=_other))
        if offhand:
            handlers.append(
                _EquippedItemObservation(['offhand'], self._items, _default=_default, _other=_other))
        if armor:
            handlers.extend([
                _EquippedItemObservation([slot], self._items, _default=_default, _other=_other)
                for slot in mc.EQUIPMENT_SLOTS if slot not in ["mainhand", "offhand"]
            ])
        super().__init__(handlers)

    def __eq__(self, other):
        return (
                super().__eq__(other)
                and other.mainhand == self.mainhand
                and other.offhand == self.offhand
                and other.armor == self.armor
        )

    def __or__(self, other):
        return EquippedItemObservation(
            items=list(set(self._items) | set(other._items)),
            mainhand=self.mainhand or other.mainhand,
            offhand=self.offhand or other.offhand,
            armor=self.armor or other.armor,
            _other=self._other,
            _default=self._default
        )


# This handler grouping doesn't really correspond nicely to the stubbed version of
# observations and violates our conventions a bit.
# Eventually this will need to be consolidated.
class _EquippedItemObservation(TranslationHandlerGroup):
    def to_string(self) -> str:
        return "_".join([str(k) for k in self.keys])

    def __init__(self,
                 dict_keys: List[str],
                 items: List[str],
                 _default,
                 _other):
        self.keys = dict_keys

        super().__init__(handlers=[
            _ItemIDObservation(self.keys, items, _default=_default, _other=_other),
            _DamageObservation(self.keys, type_str="damage"),
            _DamageObservation(self.keys, type_str="maxDamage")
        ])


class _ItemIDObservation(TranslationHandler):
    """
    Returns the item list string of the tool in the given hand.
    """

    def __init__(self, keys: List[str], items: list, _default: str, _other: str):
        """
        Initializes the space of the handler with a spaces.Dict
        of all of the spaces for each individual command.
        """
        self._items = sorted(items)
        util.error_on_malformed_item_list(self._items, [_default, _other])
        self._keys = keys
        self._default = _default
        self._other = _other
        if _other not in self._items or _default not in self._items:
            print(self._items)
            print(_default)
            print(_other)
        assert self._other in items
        assert self._default in items
        super().__init__(
            spaces.Enum(*self._items, default=self._default)
        )

    def to_string(self):
        return 'type'
        # TODO(shwang): Maybe rename this to 'item_id'?
        #   This field can contain more than just the type now -- also it can contain
        #   the metadata. (For example, it can be "sandstone" or "sandstone#2").

    def from_hero(self, obs_dict):
        try:
            head = obs_dict['equipped_items']
            for key in self._keys:
                head = head[key]
            item_type = head['type']
            metadata = head['metadata']
            assert metadata in range(16)
            item_id = util.get_unique_matching_item_list_id(self._items, item_type, metadata)
            if item_id is None:
                return self._other
            else:
                return item_id
        except KeyError:
            return self._default

    def from_universal(self, obs) -> str:
        try:
            if self._keys[0] == 'mainhand' and len(self._keys) == 1:
                offset = -9
                hotbar_index = obs['hotbar']
                if obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerPlayer':
                    offset -= 1

                equip_slot = obs['slots']['gui']['slots'][offset + hotbar_index]
                if len(equip_slot.keys()) == 0:
                    return self._default

                item_type = mc.strip_item_prefix(equip_slot['name'])
                metadata = equip_slot['variant']
                assert metadata in range(16)
                if item_type == 'air':
                    return self._default

                item_id = util.get_unique_matching_item_list_id(
                    self._items, item_type, metadata)
                if item_id is None:
                    if os.environ.get("MINERL_DEBUG_LOG", False):
                        print(f"Unknown item: '{item_type}#{metadata}'")
                    return self._other
                else:
                    return item_id
            else:
                raise NotImplementedError('type not implemented for hand type' + str(self._keys))
        except KeyError:
            # No item in hotbar slot - return 'none'
            # This looks wierd, but this will happen if the obs doesn't show up in the univ json.
            return self._default

    def __or__(self, other):
        """
        Combines two TypeObservation's (self and other) into one by 
        taking the union of self.items and other.items
        """
        if isinstance(other, _ItemIDObservation):
            return _ItemIDObservation(self._keys, list(set(self._items + other._items)),
                                      _other=self._other, _default=self._default)
        else:
            raise TypeError('Operands have to be of type TypeObservation')

    def __eq__(self, other):
        return self._keys == other._keys and self._items == other._items


class _DamageObservation(TranslationHandler):
    """
    Returns a damage observation from a type str.
    """

    def __init__(self, keys: List[str], type_str: str):
        """
        Initializes the space of the handler with a spaces.Dict
        of all of the spaces for each individual command.
        """

        self._keys = keys
        self.type_str = type_str
        self._default = 0
        super().__init__(spaces.Box(low=-1, high=1562, shape=(), dtype=int))

    def to_string(self):
        return self.type_str

    def from_hero(self, info):
        try:
            head = info['equipped_items']
            for key in self._keys:
                head = head[key]
            return np.array(head[self.type_str])
        except KeyError:
            return np.array(self._default, dtype=self.space.dtype)

    def from_universal(self, obs):
        try:
            if self._keys[0] == 'mainhand' and len(self._keys) == 1:
                offset = -9
                hotbar_index = obs['hotbar']
                if obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerPlayer':
                    offset -= 1
                return np.array(obs['slots']['gui']['slots'][offset + hotbar_index][self.type_str], dtype=np.int32)
            else:
                raise NotImplementedError('damage not implemented for hand type' + str(self._keys))
        except KeyError:
            return np.array(self._default, dtype=np.int32)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._keys == other._keys and self.type_str == other.type_str
