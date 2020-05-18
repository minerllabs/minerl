import logging
from typing import Tuple

import gym
import gym.spaces
import numpy as np

from herobraine.hero import AgentHandler, mc
from herobraine.hero.spaces import Text

from minerl.env import spaces as minerl_spaces


def strip_of_prefix(minecraft_name):
    # Names in minecraft start with 'minecraft:', like:
    # 'minecraft:log', or 'minecraft:cobblestone'
    if minecraft_name.startswith('minecraft:'):
        return minecraft_name[len('minecraft:'):]

    return minecraft_name

class ObservationFromFullStats(AgentHandler):
    logger = logging.getLogger(__name__ + ".ObservationFromFullStats")

    @staticmethod
    def to_string():
        return 'observation_from_full_stats'

    @staticmethod
    def command_list():
        return ['XPos', 'ZPos', ]

    def __init__(self):
        space = gym.spaces.Box(0, 1, [6], dtype=np.float32)
        super().__init__(space)

    def from_universal(self, x):
        try:
            return self.space.sample()
        except NotImplementedError:
            raise NotImplementedError('Observation from full state not implementing from_universal')

class POVObservation(AgentHandler):
    """
    Handles POV observations.
    """
    logger = logging.getLogger(__name__ + ".POVObservation")

    @staticmethod
    def to_string():
        return 'pov'

    def __init__(self, video_resolution: Tuple[int, int], include_depth: bool = False):
        self.include_depth = include_depth
        self.video_resolution = video_resolution
        if include_depth:
            space = gym.spaces.Box(0, 255, list(video_resolution)[::-1] + [4], dtype=np.uint8)
            self.video_depth = 4

        else:
            space = gym.spaces.Box(0, 255, list(video_resolution)[::-1] + [3], dtype=np.uint8)
            self.video_depth = 3
        self.video_height = video_resolution[0]
        self.video_width = video_resolution[1]

        super().__init__(space)

    def add_to_mission_spec(self, mission_spec):
        if self.include_depth:
            mission_spec.requestVideoWithDepth(*self.video_resolution)
        else:
            mission_spec.requestVideo(*self.video_resolution)

    def from_universal(self, obs):
        if "pov" in obs:
            assert not np.isnan(np.sum(obs["pov"])), "NAN in observation!"
            return obs["pov"]
        else:
            self.logger.warning("No video found in universal observation! Yielding 0 image.")
            return self.space.sample() * 0

    def from_hero(self, obs):
        # process the video frame
        if "video" in obs:
            return obs["video"]
        else:
            self.logger.warning("No video found in observation! Yielding 0 image.")
            return self.space.sample() * 0


class GUIContainerObservation(AgentHandler):
    """
    Handles GUI Container Observations.
    # Todo investigate obs['inventoryAvailable']
     In addition to this information, whether {{{flat}}} is true or false, an array called "inventoriesAvailable" will also be returned.
                This will contain a list of all the inventories available (usually just the player's, but if the player is pointed at a container, this
                will also be available.)
    """

    ITEM_ATTRS = [
        "item",
        "variant",
        "size"
    ]

    @staticmethod
    def to_string():
        return 'gui_container'

    def __init__(self, container_name, num_slots):
        super().__init__(gym.spaces.Tuple([
            gym.spaces.MultiDiscrete([len(mc.MC_ITEM_IDS), 16, 64]) for _ in range(num_slots)]))
        self.container_name = container_name
        self.num_slots = num_slots

    def from_universal(self, x):
        raise NotImplementedError('from_universal not implemented in GuiContainerObservation')

    def from_hero(self, obs):
        """
        Converts the Hero observation into a one-hot of the inventory items
        for a given inventory container.
        :param obs:
        :return:
        """
        keys = [k for k in obs if k.startswith(self.container_name)]
        hotbar_vec = [[0] * len(GUIContainerObservation.ITEM_ATTRS)
                      for _ in range(self.num_slots)]
        for k in keys:
            normal_k = k.split(self.container_name + "_")[-1]
            sid, attr = normal_k.split("_")

            # Parse the attribute.
            if attr == "item":
                val = mc.get_item_id(obs[k])
            elif attr == "variant":
                val = 0  # Todo: Implement variants
            elif attr == "size":
                val = int(obs[k])
            else:
                # Unknown type is not supported!
                # Todo: Investigate unknown types.
                break

            # Add it to the vector.
            attr_id = GUIContainerObservation.ITEM_ATTRS.index(attr)
            hotbar_vec[int(sid)][int(attr_id)] = val

        return hotbar_vec


class FlatInventoryObservation(AgentHandler):
    """
    Handles GUI Container Observations for selected items
    """

    @staticmethod
    def to_string():
        return 'inventory'

    def to_hero(self, x) -> str:
        raise NotImplementedError('FlatInventoryObservation must implement to_hero')

    logger = logging.getLogger(__name__ + ".FlatInventoryObservation")

    def __init__(self, item_list):
        super().__init__(gym.spaces.Dict(spaces={
            k: gym.spaces.Box(low=0, high=2304, shape=(), dtype=np.int) 
            for k in item_list
        }))
        self.num_items = len(item_list)
        self.items = item_list

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
        item_vec = [0 for _ in self.items]
        if 'inventory' in obs:
            # TODO change to map
            for stack in obs['inventory']:
                if 'type' in stack and 'quantity' in stack:
                    try:
                        i = self.items.index(stack['type'])
                        item_vec[i] += stack['quantity']
                    except ValueError:
                        continue
        else:
            self.logger.warning("No inventory found in malmo observation! Yielding empty inventory.")
            self.logger.warning(obs)

        return item_vec

    def from_universal(self, obs):
        item_vec = [0 for _ in self.items]

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
                    name = strip_of_prefix(stack['name'])
                    name = 'log' if name == 'log2' else name
                    i = self.items.index(name)
                    item_vec[i] += stack['count']
                except (KeyError, ValueError):
                    continue

        except KeyError as e:
            self.logger.warning("KeyError found in universal observation! Yielding empty inventory.")
            self.logger.error(e)
            return item_vec

        return item_vec


class DeathObservation(AgentHandler):

    @staticmethod
    def to_string():
        return 'alive'

    def from_hero(self, obs_dict):
        return obs_dict["IsAlive"] if "IsAlive" in obs_dict else True


class HotbarObservation(GUIContainerObservation):
    """
    Handles hotbar observation.
    """

    @staticmethod
    def to_string():
        return 'hotbar'

    def __init__(self):
        super().__init__("Hotbar", 9)

    def add_to_mission_spec(self, mission_spec):
        mission_spec.observeHotBar()


# class DurabilityObservation(AgentHandler):
#     """
#     Counts the remining damage left on a pickaxe.
#     """
#
#     @staticmethod
#     def to_string():
#         return 'durability'
#
#     def __init__(self):
#         super().__init__("Durability", 1562)
#
#     def from_universal(self, obs):
#         try:
#             hotbar_index = obs['hotbar']
#             max_damage = obs['slots']['inventory'][hotbar_index]['maxDamage']
#             damage = obs['slots']['inventory'][hotbar_index]['damage']
#             if max_damage > 0:
#                 return np.array(max_damage - damage, dtype=np.int32)
#             else:
#                 return np.zeros([1], dtype=np.int32)
#         except KeyError:
#             return self.space.sample()
#
#     def add_to_mission_spec(self, mission_spec):
#         raise NotImplementedError('add_to_mission_spec not implemented for DurabilityObservation')
#         # mission_spec.observeEquipedDurrability()



class TypeObservation(AgentHandler):
    """
    Returns the item list index  of the tool in the given hand
    List must start with 'none' as 0th element and end with 'other' as wildcard element
    """

    def __init__(self, hand: str, items: list):
        """
        Initializes the space of the handler with a gym.spaces.Dict
        of all of the spaces for each individual command.
        """
        self._items = items
        self._hand = hand
        self._univ_items = ['minecraft:' + item for item in items]
        self._default = 0  # 'none'
        self._other = len(items) - 1  # 'other'
        assert(items.index('none') == self._default)
        assert(items.index('other') == self._other)
        super().__init__(minerl_spaces.Enum(*self._items))

    @property
    def items(self):
        return self._items

    @property
    def universal_items(self):
        return self._univ_items

    @property
    def hand(self):
        return self._hand

    @property
    def default(self):
        return self._default

    @staticmethod
    def to_string():
        return 'type'

    def from_universal(self, obs):
        try:
            if self._hand == 'mainhand':
                offset = -9
                hotbar_index = obs['hotbar']
                if obs['slots']['gui']['type'] == 'class net.minecraft.inventory.ContainerPlayer':
                    offset -= 1
                return np.array(
                    self._univ_items.index(obs['slots']['gui']['slots'][offset + hotbar_index]['name']), dtype=np.int32)
            else:
                raise NotImplementedError('type not implemented for hand type' + self._hand)
        except KeyError:
            # No item in hotbar slot - return 'none'
            return np.array(self._default, dtype=np.int32)
        except ValueError:
            return np.array(self._other, dtype=np.int32)



    def add_to_mission_spec(self, mission_spec):
        raise NotImplementedError('add_to_mission_spec not implemented for TypeObservation')
        # mission_spec.observeEquipedDurrability()


class DamageObservation(AgentHandler):
    """
    Returns the item list index  of the tool in the given hand
    List must start with 'none' as 0th element and end with 'other' as wildcard element
    """

    def __init__(self, hand: str):
        """
        Initializes the space of the handler with a gym.spaces.Dict
        of all of the spaces for each individual command.
        """

        self._hand = hand
        self._default = 0  # 'none'
        super().__init__(gym.spaces.Discrete(1562))

    @property
    def items(self):
        return self._items

    @property
    def universal_items(self):
        return self._univ_items

    @property
    def hand(self):
        return self._hand

    @property
    def default(self):
        return self._default

    @staticmethod
    def to_string():
        return 'damage'

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


class MaxDamageObservation(AgentHandler):
    """
    Returns the item list index  of the tool in the given hand
    List must start with 'none' as 0th element and end with 'other' as wildcard element
    """

    def __init__(self, hand: str):
        """
        Initializes the space of the handler with a gym.spaces.Dict
        of all of the spaces for each individual command.
        """

        self._hand = hand
        self._default = 0  # 'none'
        super().__init__(gym.spaces.Discrete(1562))

    @property
    def items(self):
        return self._items

    @property
    def universal_items(self):
        return self._univ_items

    @property
    def hand(self):
        return self._hand

    @property
    def default(self):
        return self._default

    @staticmethod
    def to_string():
        return 'maxDamage'

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


class PlayerInventoryObservation(GUIContainerObservation):
    """
    Handles player inventory observations.
    """

    @staticmethod
    def to_string():
        return 'normal_inventory'

    def __init__(self):
        super().__init__("InventorySlot", 41)

    def add_to_mission_spec(self, mission_spec):
        mission_spec.observeFullInventory()

    def from_universal(self, x):
        # Todo: Universal
        pass


class CompassObservation(AgentHandler):
    """
    Handles compass observations.
    """
    logger = logging.getLogger(__name__ + ".CompassObservation")

    @staticmethod
    def to_string():
        return 'compassAngle'


    def __init__(self):

        super().__init__(gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32))

    def add_to_mission_spec(self, mission_spec):
        mission_spec.observeCompass()

    def from_universal(self, obs):
        if "compass" in obs and "angle" in obs["compass"]:
            y = [((obs["compass"]["angle"] * 360.0 + 180) % 360.0) - 180]
            return y
        else:
            self.logger.warning("No compass angle found in universal observation! Yielding random angle.")
            return self.space.sample()

    def from_hero(self, obs):
        # TODO np datatype parameter support for compressed replay buffers
        # process the compass handler
        if "angle" in obs:
            t = np.array([(obs['angle'] + 0.5) % 1.0]); return t
        else:
            print(obs)
            self.logger.warning("No compass found in observation! Yielding random angle.")
            return self.space.sample()

class CompassDistanceObservation(AgentHandler):
    """
    Handles compass observations.
    """
    logger = logging.getLogger(__name__ + ".CompassDistanceObservation")

    @staticmethod
    def to_string():
        return 'compass_distance'

    def __init__(self):

        super().__init__(gym.spaces.Box(low=0, high=128, shape=(1,), dtype=np.uint8))

    def add_to_mission_spec(self, mission_spec):
        mission_spec.observeCompass()

    def from_universal(self, obs):
        if "compass" in obs and "distance" in obs["compass"]:
            return [obs['compass']['distance']]
        else:
            self.logger.warning("No compass angle found in universal observation! Yielding random distance.")
            return self.space.sample()

    def from_hero(self, obs):
        # process the compass handler
        if "distance" in obs:
            return np.array([obs['distance']])
        else:
            print(obs)
            self.logger.warning("No compass found in observation! Yielding random distance.")
            return self.space.sample()

class ChatObservation(AgentHandler):
    """
    Handles chat observations.
    """

    @staticmethod
    def to_string():
        return 'chat'

    def __init__(self):
        super().__init__(Text([1]))

    def add_to_mission_spec(self, mission_spec):
        mission_spec.observeChat()

    def from_hero(self, x):
        # Todo: From Hero
        pass


class RecentCommandsObservation(AgentHandler):
    """
    Handles recent command observations
    """

    @staticmethod
    def to_string():
        return 'recent_commands'

    def __init__(self):
        super().__init__(Text([1]))

    def add_to_mission_spec(self, mission_spec):
        mission_spec.observeRecentCommands()

    def from_hero(self, x):
        # Todo: From Heri

        pass
