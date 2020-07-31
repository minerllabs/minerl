
# TODO: Consolidate equipped_item observations!
class TypeObservation(TranslationHandler):
    """
    Returns the item list index  of the tool in the given hand
    List must start with 'none' as 0th element and end with 'other' as wildcard element
    # TODO (R): Update this dcoumentation
    """

    def __init__(self, hand: str, items: list, _default='none', _other='other'):
        """
        Initializes the space of the handler with a spaces.Dict
        of all of the spaces for each individual command.
        """
        self._items = sorted(items)
        self._hand = hand
        self._univ_items = ['minecraft:' + item for item in items]
        self._default = _default 
        self._other = _other 
        assert self._other in items
        assert self._default in items
        super().__init__(spaces.Enum(*self._items, default=self._default))

    @property
    def items(self):
        return self._items

    @property
    def universal_items(self):
        return self._univ_items

    @property
    def hand(self):
        return self._hand

    def proc(self, hero_obs):
        minerl_obs = {}
        for o in self.task.observation_handlers:
            minerl_obs[o.to_string()] = o.from_hero(hero_obs)



    @property
    def default(self):
        return self._default

    def to_string(self):
        return 'equipped_items.{}.type'.format(self._hand)

    def from_hero(self, obs_dict):
        try:
            item = obs_dict['equipped_item']['mainhand']['type']
            return (self._other if item not in self._items else item)
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
            return self._default
        except ValueError:
            return  self._other

    def add_to_mission_spec(self, mission_spec):
        raise NotImplementedError('add_to_mission_spec not implemented for TypeObservation')
        # mission_spec.observeEquipedDurrability()

    def __or__(self, other):
        """
        Combines two TypeObservation's (self and other) into one by 
        taking the union of self.items and other.items
        """
        if isinstance(other, TypeObservation):
            return TypeObservation(self.hand, list(set(self.items + other.items)))
        else:
            raise TypeError('Operands have to be of type TypeObservation')

    def __eq__(self, other):
        return self.hand == other.hand and self.items == other.items


class DamageObservation(TranslationHandler):
    """
    Returns the item list index  of the tool in the given hand
    List must start with 'none' as 0th element and end with 'other' as wildcard element
    """

    def __init__(self, hand: str):
        """
        Initializes the space of the handler with a spaces.Dict
        of all of the spaces for each individual command.
        """

        self._hand = hand
        self._default = 0  
        super().__init__(spaces.Box(low=-1, high=1562, shape=(), dtype=np.int))

    @property
    def hand(self):
        return self._hand

    @property
    def default(self):
        return self._default

    def to_string(self):
        return 'equipped_items.{}.damage'.format(self._hand)

    def from_hero(self, obs):
        try:
            return np.array(info['equipped_items']['mainhand']['currentDamage'])
        except KeyError:
            return np.array(self._default, dtype=self.space.dtype)

    def from_universal(self, obs):
        try:
            if self._hand == 'mainhand':
                offset = -9
                hotbar_index = obs['hotbar']
                if obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerPlayer':
                    offset -= 1
                if obs['slots']['gui']['slots'][offset + hotbar_index]['maxDamage'] > 0:
                    return np.array(obs['slots']['gui']['slots'][offset + hotbar_index]['damage'], dtype=np.int32)
                else:
                    return np.array(self._default, dtype=np.int32)
            else:
                raise NotImplementedError('damage not implemented for hand type' + self._hand)
        except KeyError:
            return np.array(self._default, dtype=np.int32)

    def add_to_mission_spec(self, mission_spec):
        raise NotImplementedError('add_to_mission_spec not implemented for TypeObservation')

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._hand == other._hand


class MaxDamageObservation(AgentHandler):
    """
    Returns the current damage of an item.
    """

    def __init__(self, hand: str):
        """
        Initializes the space of the handler with a spaces.Dict
        of all of the spaces for each individual command.
        """

        self._hand = hand
        self._default = 0 
        super().__init__(spaces.Box(low=-1, high=1562, shape=(), dtype=np.int))

    @property
    def hand(self):
        return self._hand

    @property
    def default(self):
        return self._default

    def to_string(self):
        return 'equipped_items.{}.maxDamage'.format(self._hand)

    def from_hero(self, info):
        try:
            return np.array(info['equipped_items']['mainhand']['maxDamage'])
        except KeyError:
            return np.array(self._default, dtype=self.space.dtype)

    def from_universal(self, obs):
        try:
            if self._hand == 'mainhand':
                offset = -9
                hotbar_index = obs['hotbar']
                if obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerPlayer':
                    offset -= 1
                return np.array(obs['slots']['gui']['slots'][offset + hotbar_index]['maxDamage'], dtype=np.int32)
            else:
                raise NotImplementedError('damage not implemented for hand type' + self._hand)
        except KeyError:
            return np.array(self._default, dtype=np.int32)

    def add_to_mission_spec(self, mission_spec):
        raise NotImplementedError('add_to_mission_spec not implemented for TypeObservation')

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._hand == other._hand

