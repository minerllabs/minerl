# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import logging
from typing import List, Optional

import jinja2
from minerl.herobraine.hero.handlers.translation import TranslationHandler
import numpy as np
from minerl.herobraine.hero import spaces
import minerl.herobraine.hero.mc as mc


def _univ_obs_get_inventory_slots(obs: dict) -> Optional[List[dict]]:
    """
    Observations in univ.json contain "slot dicts" containing info about
    items held in player or container inventories. This function processes an obs dict
    from univ.json, and returns
    the list of "slot" dictionaries, where every non-empty dictionary corresponds to
    an item stack.

    See the following link for an example format:
    https://gist.github.com/shwang/9c8815e952eb2a4c308aea09f112cd6a#file-univ-head-json-L162
    """
    # If these keys don't exist, then we should KeyError.
    gui_type = obs['slots']['gui']['type']
    gui_slots = obs['slots']['gui']['slots']

    if gui_type in ('class net.minecraft.inventory.ContainerPlayer',
                    'class net.minecraft.inventory.ContainerWorkbench'):
        slots = gui_slots[1:]
    elif gui_type == 'class net.minecraft.inventory.ContainerFurnace':
        slots = gui_slots[0:2] + gui_slots[3:]
    else:
        slots = gui_slots

    # Add in the cursor item tracking only if present.
    cursor_item = gui_slots.get('cursor_item')
    if cursor_item is not None:
        slots.append(cursor_item)


class FlatInventoryObservation(TranslationHandler):
    """
    Handles GUI Container Observations for selected items
    """

    def to_string(self):
        return 'inventory'

    def xml_template(self) -> str:
        return str(
            """<ObservationFromFullInventory flat="false"/>""")

    logger = logging.getLogger(__name__ + ".FlatInventoryObservation")

    def __init__(self, item_list, _other='other'):
        item_list = sorted(item_list)
        super().__init__(spaces.Dict(spaces={
            k: spaces.Box(low=0, high=2304,
                          shape=(), dtype=np.int32, normalizer_scale='log')
            for k in item_list
        }))
        self.num_items = len(item_list)
        self.items = item_list

    def add_to_mission_spec(self, mission_spec):
        pass
        # Flat obs not supported by API for some reason - should be mission_spec.observeFullInventory(flat=True)

    def from_hero(self, info):
        """
        Converts the Hero observation into a one-hot of the inventory items
        for a given inventory container. Ignores variant / color
        :param obs:
        :return:
        """
        item_dict = self.space.no_op()
        # TODO: RE-ADDRESS THIS DUCK TYPED INVENTORY DATA FORMAT WHEN MOVING TO STRONG TYPING
        for stack in info['inventory']:
            if 'type' in stack and 'quantity' in stack:
                type_name = stack['type']
                if type_name == 'log2' and 'log2' not in self.items:
                    type_name = 'log'
                if type_name in item_dict:
                    # This sets the number of air to correspond to the number of empty slots :)
                    if type_name == "air":
                        item_dict[type_name] += 1
                    else:
                        item_dict[type_name] += stack["quantity"]

        return item_dict

    def from_universal(self, obs):
        item_dict = self.space.no_op()

        try:
            slots = _univ_obs_get_inventory_slots(obs)

            # Add from all slots
            for stack in slots:
                try:
                    name = mc.strip_item_prefix(stack['name'])
                    name = 'log' if name == 'log2' else name
                    if name == "air":
                        item_dict[name] += 1
                    else:
                        item_dict[name] += stack['count']
                except (KeyError, ValueError):
                    continue

        except KeyError as e:
            self.logger.warning("KeyError found in universal observation! Yielding empty inventory.")
            self.logger.error(e)
            return item_dict

        return item_dict

    def __or__(self, other):
        """
        Combines two flat inventory observations into one by taking the
        union of their items.
        Asserts that other is also a flat observation.
        """
        assert isinstance(other, FlatInventoryObservation)
        return FlatInventoryObservation(list(set(self.items) | (set(other.items))))

    def __eq__(self, other):
        return isinstance(other, FlatInventoryObservation) and \
               (self.items) == (other.items)


def _get_variant_item_name(item_type: str, variant: str) -> str:
    return f"{item_type}_{variant}"


class FlatInventoryVariantObservation(FlatInventoryObservation):
    """
    Handles GUI Container Observations for selected items
    """

    def to_string(self):
        return 'inventory_variant'

    logger = logging.getLogger(__name__ + ".FlatInventoryVariantObservation")

    def from_hero(self, info):
        """
        Converts the Hero observation into a one-hot of the inventory items
        for a given inventory container. Ignores variant / color
        :param obs:
        :return:
        """
        item_dict = self.space.no_op()
        for stack in info['inventory']:
            if 'variant' in stack:
                assert 'name' in stack and 'quantity' in stack
                variant_item_name = _get_variant_item_name(
                    stack['type'], stack['variant'])
                # "half" types end up in stack['variant'] and we don't care
                # about them (example: double_plant_lower, door_lower)
                if variant_item_name in item_dict:
                    item_dict[variant_item_name] += stack['quantity']

        return item_dict

    def from_universal(self, obs):
        item_dict = self.space.no_op()
        slots = _univ_obs_get_inventory_slots(obs)
        expected_stack_keys = ['type', 'variant', 'quantity']
        for stack in slots:
            for key in expected_stack_keys:
                if key not in stack:
                    continue
            item_type = mc.strip_item_prefix(stack['name'])
            variant = stack['variant']
            quantity = stack['quantity']
            variant_item_name = _get_variant_item_name(item_type, variant)
            if variant_item_name in item_dict:
                item_dict[variant_item_name] += quantity
        return item_dict

    def __or__(self, other):
        """
        Combines two flat inventory observations into one by taking the
        union of their items.
        Asserts that other is also a flat observation.
        """
        assert isinstance(other, FlatInventoryVariantObservation)
        return FlatInventoryVariantObservation(list(set(self.items) | (set(other.items))))

    def __eq__(self, other):
        return isinstance(other, FlatInventoryVariantObservation) and \
               (self.items) == (other.items)
