# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import logging

from minerl.herobraine.hero.handlers.agent import action
from minerl.herobraine.hero.handlers import util
import minerl.herobraine.hero.mc as mc


class EquipAction(action.ItemWithMetadataListAction):
    """
    An action handler for observing a list of equipped items
    """

    logger = logging.getLogger(__name__ + ".EquipAction")

    def __init__(self, items: list, _default='none', _other='other'):
        """
        Initializes the space of the handler to be one for each item in the list plus one for the
        default no-craft action
        """
        super().__init__("equip", items, _default=_default, _other=_other)
        self.previous = self._default

    def xml_template(self) -> str:
        return str("<EquipCommands/>")

    def reset(self):
        self.previous = self._default

    def from_universal(self, obs) -> str:
        slots_gui_type = obs['slots']['gui']['type']
        if slots_gui_type == 'class net.minecraft.inventory.ContainerPlayer':
            hotbar_index = int(obs['hotbar'])
            hotbar_slot = obs['slots']['gui']['slots'][-10 + hotbar_index]

            item_type = mc.strip_item_prefix(hotbar_slot['name'])
            metadata = hotbar_slot['variant']
            id = util.get_unique_matching_item_list_id(self.items, item_type, metadata,
                                                       clobber_logs=False)
            if id is None:
                id = "other"

            # TODO(shwang): Tell Brandon that this is a change in behavior (probably ok?)
            #   Consecutive "other" now results in "none". It used to be the case that
            #   "other" would always be returned regardless of repetition and whether
            #   ground-truth-"other" equipped items were being changed. This behavior
            #   was different from the behavior of other keys.
            if id == self.previous:
                return self._default
            else:
                self.previous = id
                return id
        else:
            self.logger.warning(f"Unexpected slots_gui_type={slots_gui_type}, "
                                f"Abandoning processing and simply returning {self._default}"
                                )
            return self._default
