# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

from minerl.herobraine.hero.handlers.agent.action import ItemListAction


class EquipAction(ItemListAction):
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
        self._items = items
        self._command = 'equip'
        super().__init__(self._command, self._items, _default=_default, _other=_other),
        self.previous = self._default

    def to_hero(self, x):
        assert isinstance(x, str)

        # Add a delimiter if necessary and check for problem cases
        n_delimiter = x.count('#')
        if n_delimiter == 1:
            # Validate "adjective" and then send proceed.
            item_type, metadata_str = x.split('#')
            assert len(item_type) > 0
            assert int(metadata_str) in range(16)
            return super().to_hero(x)
        elif n_delimiter == 0:
            return self.to_hero(f"{x}#0")
        else:
            raise ValueError(f"Too many delimiters '#' in x='{x}'.")

    def from_universal(self, obs):
        try:
            if obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerPlayer':
                hotbar_index = int(obs['hotbar'])
                item = self._univ_items.index(obs['slots']['gui']['slots'][-10 + hotbar_index]['name'])
                if item != self.previous:
                    self.previous = item
                    return obs['slots']['gui']['slots'][-10 + hotbar_index]['name'].split('minecraft:')[-1]
        except KeyError:
            return self._default
        except ValueError:
            return self._other
        return self._default

    def reset(self):
        self.previous = self._default
