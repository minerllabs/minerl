# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton


from minerl.herobraine.hero.handlers.agent.observations.compass import CompassObservation
from minerl.herobraine.hero.handlers.agent.observations.inventory import FlatInventoryObservation
from minerl.herobraine.hero.handlers.agent.observations.equipped_item import _ItemIDObservation
from minerl.herobraine.hero.handlers.agent.action import ItemListAction


def test_merge_item_list_command_actions():
    class TestItemListCommandAction(ItemListAction):
        def __init__(self, items: list, **item_list_kwargs):
            super().__init__("test", items, **item_list_kwargs)

        def to_string(self):
            return "test_item_list_command"

    left = TestItemListCommandAction(['none', 'A', 'B', 'C', 'D'], _other='none')
    right = TestItemListCommandAction(['none', 'E', 'F'], _other='none')
    merged = left | right
    expected_merged = TestItemListCommandAction(['none', 'A', 'B', 'C', 'D', 'E', 'F'],
                                                _other='none')
    assert merged == expected_merged


def test_merge_type_observation():
    type_obs_a = _ItemIDObservation('test', ['none', 'A', 'B', 'C', 'D', 'other'], _default='none',
                                    _other='other')
    type_obs_b = _ItemIDObservation('test', ['none', 'E', 'F', 'other'], _default='none',
                                    _other='other')
    type_obs_result = _ItemIDObservation('test', ['none', 'A', 'B', 'C', 'D', 'E', 'F', 'other'],
                                         _default='none', _other='other')
    merged = type_obs_a | type_obs_b
    assert merged == type_obs_result


def test_merge_flat_inventory_observation():
    assert FlatInventoryObservation(['stone', 'sandstone', 'lumber', 'wood', 'iron_bar']
                                    ) | FlatInventoryObservation(['ice', 'water']) == \
           FlatInventoryObservation(['stone', 'sandstone', 'lumber', 'wood', 'iron_bar',
                                     'ice', 'water'])


def test_combine_compass_observations():
    assert CompassObservation() | CompassObservation() == CompassObservation()
