# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import logging

import jinja2
from minerl.herobraine.hero.handlers.translation import TranslationHandler
import numpy as np
from minerl.herobraine.hero import spaces
import minerl.herobraine.hero.mc as mc


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
                if type_name == 'log2':
                    type_name = 'log'

                # This sets the nubmer of air to correspond to the number of empty slots :)
                try:
                    if type_name == "air":
                        item_dict[type_name] += 1
                    else:
                        item_dict[type_name] += stack["quantity"]
                except KeyError:
                    # We only care to observe what was specified in the space.
                    continue

        return item_dict

    def from_universal(self, obs):
        item_dict = self.space.no_op()

        try:
            if obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerPlayer' or \
                    obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerWorkbench':
                slots = obs['slots']['gui']['slots'][1:]
            elif obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerFurnace':
                slots = obs['slots']['gui']['slots'][0:2] + obs['slots']['gui']['slots'][3:]
            else:
                slots = obs['slots']['gui']['slots']

            # Add in the cursor item tracking if present
            try:
                slots.append(obs['slots']['gui']['cursor_item'])
            except KeyError:
                pass

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
