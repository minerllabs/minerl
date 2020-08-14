# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton


from minerl.herobraine.hero.handlers.agent.action import Action, ItemListAction
import jinja2
import minerl.herobraine.hero.spaces as spaces

class CraftAction(ItemListAction):
    """
    An action handler for crafting items

        Note when used along side Craft Item Nearby, block lists must be disjoint or from_universal will fire multiple
        times

    """
    _command = "craft"

    def to_string(self):
        return "craft"

    def xml_template(self) -> str:
        return str("<SimpleCraftCommands/>")


    def __init__(self, items: list, **item_list_kwargs):
        """
        Initializes the space of the handler to be one for each item in the list plus one for the
        default no-craft action (command 0)

        Items are minecraft resource ID's
        """
        super().__init__(
            self._command, items, **item_list_kwargs)

    def from_universal(self, obs):
        if 'diff' in obs and 'crafted' in obs['diff'] and len(obs['diff']['crafted']) > 0:
            try:
                x =  self._univ_items.index(obs['diff']['crafted'][0]['item'])
                return obs['diff']['crafted'][0]['item'].split('minecraft:')[-1]
            except ValueError:
                return self._default
                # return self._items.index('other')
        else:
            return self._default



class CraftNearbyAction(CraftAction):
    """
    An action handler for crafting items when agent is in view of a crafting table

        Note when used along side Craft Item, item lists must be disjoint or from_universal will fire multiple times

    """
    _command = "craftNearby"

    def to_string(self):
        return 'nearbyCraft'

    def xml_template(self) -> str:
        return str("<NearbyCraftCommands/>")
