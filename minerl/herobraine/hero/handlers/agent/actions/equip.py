# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

from minerl.herobraine.hero.handlers.agent import action


class EquipAction(action.ItemWithMetadataListAction):
    """
    An action handler for observing a list of equipped items
    """

    def to_string(self):
        return 'equip'

    def xml_template(self) -> str:
        return str("<EquipCommands/>")

    def __init__(self, items: list, _default='none', _other='other'):
        """
        Initializes the space of the handler to be one for each item in the list plus one for the
        default no-craft action
        """
        super().__init__("equip", items, _default=_default, _other=_other)
        self.previous = self._default

    def from_universal(self, obs):
        if obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerPlayer':
            hotbar_index = int(obs['hotbar'])
            hotbar_slot = obs['slots']['gui']['slots'][-10 + hotbar_index]
            item = self._univ_items.index(hotbar_slot['name'])
            if item != self.previous:
                self.previous = item
                return hotbar_slot.split('minecraft:')[-1]

        return self._default

    def reset(self):
        self.previous = self._default
