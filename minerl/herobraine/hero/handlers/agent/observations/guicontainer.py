# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

"""
Note that this file contains unimplemented functionality 
and remains as a stub for future work.
"""

# # TODO: Finish implementing GUIContainerObservation
# from minerl.herobraine.hero.handlers.translation import TranslationHandler


# class GUIContainerObservation(TranslationHandler):
#     """
#     Handles GUI Container Observations.
#     # Todo investigate obs['inventoryAvailable']
#      In addition to this information, whether {{{flat}}} is true or false, an array called "inventoriesAvailable" will also be returned.
#                 This will contain a list of all the inventories available (usually just the player's, but if the player is pointed at a container, this
#                 will also be available.)
#     """

#     ITEM_ATTRS = [
#         "item",
#         "variant",
#         "size"
#     ]

#     def to_string(self):
#         return 'gui_container'

#     def __init__(self, container_name, num_slots):
#         super().__init__(spaces.Tuple([
#             spaces.MultiDiscrete([len(mc.MC_ITEM_IDS), 16, 64], dtype=np.int32) for _ in range(num_slots)]))
#         self.container_name = container_name
#         self.num_slots = num_slots

#     def from_universal(self, x):
#         raise NotImplementedError('from_universal not implemented in GuiContainerObservation')

#     def from_hero(self, obs):
#         """
#         Converts the Hero observation into a one-hot of the inventory items
#         for a given inventory container.
#         :param obs:
#         :return:
#         """
#         keys = [k for k in obs if k.startswith(self.container_name)]
#         hotbar_vec = [[0] * len(GUIContainerObservation.ITEM_ATTRS)
#                       for _ in range(self.num_slots)]
#         for k in keys:
#             normal_k = k.split(self.container_name + "_")[-1]
#             sid, attr = normal_k.split("_")

#             # Parse the attribute.
#             if attr == "item":
#                 val = mc.get_item_id(obs[k])
#             elif attr == "variant":
#                 val = 0  # Todo: Implement variants
#             elif attr == "size":
#                 val = int(obs[k])
#             else:
#                 # Unknown type is not supported!
#                 # Todo: Investigate unknown types.
#                 break

#             # Add it to the vector.
#             attr_id = GUIContainerObservation.ITEM_ATTRS.index(attr)
#             hotbar_vec[int(sid)][int(attr_id)] = val

#         return hotbar_vec

#     def __or__(self, other):
#         """
#         Combines two gui container observations into one.
#         The new observable has the max of self and other's num_slots.
#         Container names must match.
#         """
#         if isinstance(other, GUIContainerObservation):
#             if self.container_name != other.container_name:
#                 raise ValueError("Observations can only be combined if they share a container name.")
#             return GUIContainerObservation(self.container_name, max(self.num_slots, other.num_slots))
#         else:
#             raise ValueError('Observations can only be combined with gui container observations')

#     def __eq__(self, other):
#         return (
#                 isinstance(other, GUIContainerObservation)
#                 and self.container_name == other.container_name
#                 and self.num_slots == other.num_slots)


# class HotbarObservation(GUIContainerObservation):
#     """
#     Handles hotbar observation.
#     """

#     def to_string(self):
#         return 'hotbar'

#     def __init__(self):
#         super().__init__("Hotbar", 9)

#     def add_to_mission_spec(self, mission_spec):
#         mission_spec.observeHotBar()
