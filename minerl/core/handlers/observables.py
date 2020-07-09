import logging
from enum import Enum
from typing import Tuple

import gym
import gym.spaces
import numpy as np

from minerl.core import mc
from minerl.core.handlers.agent_handler import AgentHandler
from minerl.core.spaces import Text


def strip_prefix(minecraft_name):
    # Names in minecraft start with 'minecraft:', like:
    # 'minecraft:log', or 'minecraft:cobblestone'
    if minecraft_name.startswith('minecraft:'):
        return minecraft_name[len('minecraft:'):]

    return minecraft_name


class POVObservation(AgentHandler):
    """
    Handles POV observations.
    """
    logger = logging.getLogger(__name__ + ".POVObservation")

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

    def from_universal(self, obs):
        if "pov" in obs:
            assert not np.isnan(np.sum(obs["pov"])), "NAN in observation!"
            return obs["pov"]
        else:
            self.logger.error("No video found in universal observation! Yielding 0 image.")
            return self.space.sample() * 0

    def from_hero(self, obs):
        # process the video frame
        if "video" in obs:
            return obs["video"]
        else:
            self.logger.error("No video found in observation! Yielding 0 image.")
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

    def __init__(self, container_name, num_slots):
        super().__init__(gym.spaces.Tuple([
            gym.spaces.MultiDiscrete([len(mc.MC_ITEM_IDS), 16, 64]) for _ in range(num_slots)]))
        self.container_name = container_name
        self.num_slots = num_slots

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
    logger = logging.getLogger(__name__ + ".FlatInventoryObservation")

    def __init__(self, item_list):
        super().__init__(gym.spaces.Box(low=0, high=1, shape=[len(item_list),]))
        # super().__init__(gym.spaces.Tuple(gym.spaces.MultiDiscrete(len(item_list)), gym.spaces.Box(low=0, high=1, shape=[1,])))
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
                        item_vec[i] += stack['quantity'] / 64
                    except ValueError:
                        continue
        else:
            self.logger.error("No inventory found in malmo observation! Yielding empty inventory.")
            self.logger.error(obs)

        return item_vec

    def from_universal(self, obs):
        item_vec = [0 for _ in self.items]
        if 'slots' in obs and 'inventory' in obs['slots']:
            for stack in obs['slots']['inventory']:
                if 'name' in stack and 'count' in stack:
                    try:
                        i = self.items.index(strip_prefix(stack['name']))
                        item_vec[i] += stack['count'] / 64
                    except ValueError:
                        continue
        else:
            self.logger.error("No inventory found in universal observation! Yielding empty inventory.")

        return item_vec



class DeathObservation(AgentHandler):
    def from_hero(self, obs_dict):
        return obs_dict["IsAlive"] if "IsAlive" in obs_dict else True


class HotbarObservation(GUIContainerObservation):
    """
    Handles hotbar observation.
    """

    def __init__(self):
        super().__init__("Hotbar", 9)

    def add_to_mission_spec(self, mission_spec):
        mission_spec.observeHotBar()


class PlayerInventoryObservation(GUIContainerObservation):
    """
    Handles player inventory observations.
    """

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
    logger = logging.getLogger(__name__ + ".POVObservation")

    def __init__(self):

        super().__init__(gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32))

    def add_to_mission_spec(self, mission_spec):
        mission_spec.observeCompass()

    def from_universal(self, obs):
        if "compass" in obs and "angle" in obs["compass"]:
            y = [(obs["compass"]["angle"] + 0.5) % 1.0]; return y
        else:
            self.logger.error("No compass angle found in universal observation! Yielding random angle.")
            return self.space.sample()

    def from_hero(self, obs):
        # TODO np datatype parameter support for compressed replay buffers
        # process the compass handler
        if "angle" in obs:
            t = np.array([(obs['angle'] + 0.5) % 1.0]); return t
        else:
            self.logger.error("No compass found in observation! Yielding random angle.")
            return self.space.sample()


class CompassDistanceObservation(AgentHandler):
    """
    Handles compass observations.
    """
    logger = logging.getLogger(__name__ + ".POVObservation")

    def __init__(self):

        super().__init__(gym.spaces.Box(low=0, high=128, shape=(1,), dtype=np.uint8))

    def add_to_mission_spec(self, mission_spec):
        mission_spec.observeCompass()

    def from_universal(self, obs):
        if "compass" in obs and "distance" in obs["compass"]:
            return obs['compass']['distance']
        else:
            self.logger.error("No compass angle found in universal observation! Yielding random distance.")
            return self.space.sample()

    def from_hero(self, obs):
        # process the compass handler
        if "distance" in obs:
            return np.array(obs['distance'])
        else:
            print(obs)
            self.logger.error("No compass found in observation! Yielding random distance.")
            return self.space.sample()


class ChatObservation(AgentHandler):
    """
    Handles chat observations.
    """

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

    def __init__(self):
        super().__init__(Text([1]))

    def add_to_mission_spec(self, mission_spec):
        mission_spec.observeRecentCommands()

    def from_hero(self, x):
        # Todo: From Hero
        pass


class SimpleObservationHander(AgentHandler):
    def __init__(self, keys: list, space: gym.spaces.space, default_if_missing):
        """
        Wrapper for simple
        :param keys: list of nested dictionary keys from the root of the observation dict
        :param space: gym space corresponding to the shape of the returned value
        :param default_if_missing: value for handler to take if missing in the observation dict
        """
        super().__init__(space)
        self.obs_keys = keys
        self.default_if_missing = default_if_missing
        self.human_obs_keys = '/'.join(self.obs_keys)
        self.logger = logging.getLogger(f'{__name__}.{self.human_obs_keys}')

    def from_hero(self, obs_dict):
        for key in self.obs_keys:
            if key in obs_dict:
                obs_dict = obs_dict[key]
            else:
                self.logger.error(f'No {self.obs_keys[-1]} observation! Yielding default value {self.default_if_missing}'
                                  f' for {self.human_obs_keys}')
                return np.array(self.default_if_missing)
        return np.array(obs_dict)


class LifeObservation(SimpleObservationHander):
    """
    Handles life observation / health observation. Its initial value on world creation is 20 (full bar)
    """
    def __init__(self):
        super().__init__(keys=['life'], space=gym.spaces.Box(low=0, high=mc.MAX_LIFE, shape=(), dtype=np.float),
                         default_if_missing=mc.MAX_LIFE)


class ScoreObservation(SimpleObservationHander):
    """
    Handles score observation
    """
    def __init__(self):
        super().__init__(keys=['score'], space=gym.spaces.Box(low=0, high=mc.MAX_SCORE, shape=(), dtype=np.int),
                         default_if_missing=0)


class FoodLevelObservation(SimpleObservationHander):
    """
    Handles food_level observation representing the player's current hunger level, shown on the hunger bar. Its initial
    value on world creation is 20 (full bar) - https://minecraft.gamepedia.com/Hunger#Mechanics
    """
    def __init__(self):
        super().__init__(keys=['food_level'], space=gym.spaces.Box(low=0, high=mc.MAX_FOOD, shape=(), dtype=np.int),
                         default_if_missing=mc.MAX_LIFE)


class FoodSaturationObservation(SimpleObservationHander):
    """
    Returns the food saturation observation which determines how fast the hunger level depletes and is controlled by the
     kinds of food the player has eaten. Its maximum value always equals foodLevel's value and decreases with the hunger
     level. Its initial value on world creation is 5. - https://minecraft.gamepedia.com/Hunger#Mechanics
    """
    def __init__(self):
        super().__init__(keys=['food_level'], space=gym.spaces.Box(low=0, high=mc.MAX_FOOD_SATURATION, shape=(),
                                                                   dtype=np.float), default_if_missing=5.0)


class XPObservation(SimpleObservationHander):
    """
    Handles observation of experience points 1395 experience corresponds with level 30
    - see https://minecraft.gamepedia.com/Experience for more details
    """
    def __init__(self):
        super().__init__(keys=['xp'], space=gym.spaces.Box(low=0, high=mc.MAX_XP, shape=(), dtype=np.int),
                         default_if_missing=0)


class BreathObservation(SimpleObservationHander):
    """
        Handles observation of breath which tracks the amount of air remaining before beginning to suffocate
    """
    def __init__(self):
        super().__init__(keys=['breath'], space=gym.spaces.Box(low=0, high=mc.MAX_BREATH, shape=(), dtype=np.int),
                         default_if_missing=300)
