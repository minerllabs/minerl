# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton


"""
Not very proud of the code reuse in this module -- @wguss
"""

import typing
from typing import Iterable

import jinja2
from minerl.herobraine.hero import spaces
from minerl.herobraine.hero.handlers.translation import TranslationHandler, TranslationHandlerGroup
import numpy as np
__all__ = ['EquippedItemObservation']



class EquippedItemObservation(TranslationHandlerGroup):
    """
    Enables the observation of equipped items in the main and offhand
    of the agent.
    """

    def to_string(self) -> str:
        return "equipped_items"

    def xml_template(self) -> str:
        return str(
            """<ObservationFromEquippedItem/>""")

    def __init__(self,
        items :  Iterable[str],
        mainhand : bool = True , offhand : bool = False,
        _default : str ='air',
        _other : str ='other'):

        assert mainhand or offhand, "Must select at least one hand to observer."
        assert not offhand, "Offhand equipped items is not implemented yet."
        self._hand = 'mainhand' # TODO: Implement offhand.
        self._items = items
        self._other = _other
        self._default = _default

        super().__init__(handlers= [
            _HandObservation(self._hand, items, _default= _default, _other= _other) #,
            # Eventually this can include offhand.
            ], 
        )

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and other.hand == self._hand
        )
    
    def __or__(self, other):
        return EquippedItemObservation(
            items = list(set(self._items) | set(other._items)),
            mainhand = (self._hand == 'mainhand'),
            offhand = False,
            _other= self._other,
            _default=self._default
        )

        
            
# This handler grouping doesn't really correspond nicely to the stubbed version of
# observations and violates our conventions a bit.
# Eventually this will need to be consolidated.
class _HandObservation(TranslationHandlerGroup):
    def to_string(self) -> str:
        return self.hand

    def __init__(self,
        hand : str,
        items :  typing.List[str],
        _default,
        _other):

        self.hand = hand
        
        return super().__init__(handlers=[
            _TypeObservation(hand, items, _default=_default, _other=_other),
            _DamageObservation(hand, type_str="damage"),
            _DamageObservation(hand, type_str="maxDamage")
        ])



class _TypeObservation(TranslationHandler):
    """
    Returns the item list index  of the tool in the given hand
    If _default and _other are NOT specified, list must contain all possible items
    @:param _default - Overrides the default type, "air"
    @:param _other - String to return if the observerd element is not in items
    # TODO (R): Update this documentation
    """

    def __init__(self, hand: str, items: list, _default : str, _other : str):
        """
        Initializes the space of the handler with a spaces.Dict
        of all of the spaces for each individual command.
        """
        self._items = sorted(items)
        self._hand = hand
        self._univ_items = ['minecraft:' + item for item in items]
        self._default = _default
        self._other = _other
        # assert self._other in items
        # assert self._default in items
        super().__init__(
            spaces.Enum(*self._items, default=self._default)
        )

    def to_string(self):
        return 'type'

    def from_hero(self, obs_dict):
        try:
            item = obs_dict['equipped_item']['mainhand']['type']
            # TODO properly return _other for air?
            return self._other if item not in self._items else item
        except KeyError:
            return self._default

    def from_universal(self, obs):
        try:
            if self._hand == 'mainhand':
                offset = -9
                hotbar_index = obs['hotbar']
                if obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerPlayer':
                    offset -= 1

                item_name = (
                    obs['slots']['gui']['slots'][offset + hotbar_index]['name'].split("minecraft:")[-1])
                if not item_name in self._items:
                    raise ValueError()
                if item_name == 'air':
                    raise KeyError()

                return item_name
            else: 
                raise NotImplementedError('type not implemented for hand type' + self._hand)
        except KeyError:
            # No item in hotbar slot - return 'none'
            # This looks weird, but this will happen if the obs doesn't show up in the univ json.
            return self._default
        except ValueError:
            return  self._other

    def __or__(self, other):
        """
        Combines two TypeObservation's (self and other) into one by 
        taking the union of self.items and other.items
        """
        if isinstance(other, _TypeObservation):
            return _TypeObservation(self._hand, list(set(self._items + other._items)),
                _other= self._other, _default= self._default)
        else:
            raise TypeError('Operands have to be of type TypeObservation')

    def __eq__(self, other):
        return self._hand == other._hand and self._items == other._items


class _DamageObservation(TranslationHandler):
    """
    Returns a damage observation from a type str.
    """

    def __init__(self, hand: str, type_str : str):
        """
        Initializes the space of the handler with a spaces.Dict
        of all of the spaces for each individual command.
        """

        self._hand = hand
        self.type_str = type_str
        self._default = 0 
        super().__init__(spaces.Box(low=-1, high=1562, shape=(), dtype=np.int))

    def to_string(self):
        return self.type_str

    def from_hero(self, info):
        try:
            return np.array(info['equipped_items'][self._hand][self.type_str])
        except KeyError:
            return np.array(self._default, dtype=self.space.dtype)

    def from_universal(self, obs):
        try:
            if self._hand == 'mainhand':
                offset = -9
                hotbar_index = obs['hotbar']
                if obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerPlayer':
                    offset -= 1
                return np.array(obs['slots']['gui']['slots'][offset + hotbar_index][self.type_str], dtype=np.int32)
            else:
                raise NotImplementedError('damage not implemented for hand type' + self._hand)
        except KeyError:
            return np.array(self._default, dtype=np.int32)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._hand == other._hand and self.type_str == other.type_str
