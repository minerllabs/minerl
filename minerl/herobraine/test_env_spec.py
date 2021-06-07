# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

from minerl.herobraine.env_spec import EnvSpec
import minerl.herobraine.hero.handlers as handlers


# class TestSpec(EnvSpec):
#     def __init__(self, resolution, items):
#         self.resolution = resolution
#         self.items = items
#
#     def create_actionables(self):
#         return [
#             handlers.CraftItem(self.items)
#         ]
#
#     def create_observables(self):
#         return [
#             handlers.POVObservation(self.resolution)
#         ]
#         # todo
#
#     def get_docstring(self):
#         pass
#
#     def is_from_folder(self, folder: str):
#         pass
#
#     def create_mission_handlers(self):
#         pass
#
#     def determine_success_from_rewards(self):
#         pass

# def test_to_xml():
#     """
#     Tests the env_spec to xml.
#     """
#     assert False, "test not written yet." # TODO: (@wguss)
