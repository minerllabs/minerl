# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import logging

import numpy as np

from typing import List, Sequence
from collections import defaultdict

from minerl.herobraine.hero.handlers import util
from minerl.herobraine.hero.handlers.translation import TranslationHandler
from minerl.herobraine.hero import spaces
import minerl.herobraine.hero.mc as mc


def _univ_obs_get_all_inventory_slots(obs: dict) -> List[dict]:
    """
    Observations in univ.json contain "slot dicts" containing info about
    items held in player or container inventories. This function processes an obs dict
    from univ.json, and returns
    the list of "slot" dictionaries, where every dictionary corresponds to
    an item stack. Non-empty dictionaries have "type", "metadata", and "quantity" keys.
    Empty dictionaries represent empty inventory slots, corresponding to stacks of type
    "air".

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
    cursor_item = obs['slots']['gui'].get('cursor_item')
    if cursor_item is not None:
        slots.append(cursor_item)
    return slots


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

    def __init__(self, item_list: Sequence[str], _other='other'):
        item_list = sorted(item_list)
        util.error_on_malformed_item_list(item_list, [_other])
        super().__init__(spaces.Dict(spaces={
            k: spaces.Box(low=0, high=2304,
                          shape=(), dtype=np.int32, normalizer_scale='log')
            for k in item_list
        }))
        self.num_items = len(item_list)
        self.items = item_list
        self._other = _other

    def add_to_mission_spec(self, mission_spec):
        pass
        # Flat obs not supported by API for some reason - should be mission_spec.observeFullInventory(flat=True)

    def from_hero(self, obs):
        """
        Converts the Hero observation into a one-hot of the inventory items
        for a given inventory container. Ignores variant / color
        :param obs:
        :return:
        """
        item_dict = {item_id: np.array(0) for item_id in self.items}  # Faster than Dict.no_op()
        # TODO: RE-ADDRESS THIS DUCK TYPED INVENTORY DATA FORMAT WHEN MOVING TO STRONG TYPING
        for stack in obs['inventory']:
            type_name = stack['type']
            if type_name == "air" and type_name in self.items:
                item_dict[type_name] += 1
                continue

            # "half" types end up in stack['variant'] and we don't care
            # about them (example: double_plant_lower, door_lower)
            unique = util.get_unique_matching_item_list_id(self.items, type_name, stack['metadata'])
            assert stack["quantity"] >= 0
            assert stack["metadata"] in range(16)

            # Unique should be none iff the item is not in self.items
            if unique is not None:
                item_dict[unique] += stack["quantity"]
            elif self._other in self.items:
                item_dict[self._other] += stack["quantity"]

        return item_dict

    def from_universal(self, obs):
        item_dict = {item_id: np.array(0) for item_id in self.items}  # Faster than Dict.no_op()
        try:
            slots = _univ_obs_get_all_inventory_slots(obs)

            # Add from all slots
            for stack in slots:
                item_type = mc.strip_item_prefix(stack['name']) if len(stack.keys()) != 0 else "air"

                if item_type == "air":
                    # We don't expect to actually see any slots with `stack['name'] == 'air'`,
                    # (air should be an empty dictionary stack) but if we do,
                    # `stack['name'] == 'air'` is also covered under this case.
                    if item_type in self.items:
                        # This lets us count empty slots non-default MC behavior
                        item_dict[item_type] += 1
                else:
                    unique = util.get_unique_matching_item_list_id(
                        self.items, item_type, stack['variant'])

                    # Unique should be none iff the item is not in self.items
                    if unique is not None:
                        item_dict[unique] += stack["count"]
                    elif self._other in self.items:
                        item_dict[self._other] += stack["count"]
        except KeyError as e:
            self.logger.warning("KeyError found in universal observation! Yielding empty inventory.")
            self.logger.error(e)
            return self.space.no_op()

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
