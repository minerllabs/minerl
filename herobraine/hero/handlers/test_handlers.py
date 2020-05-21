# Tests merging two item list commands
from herobraine.hero.handlers.actionable import ItemListCommandAction
from herobraine.hero.handlers.observables import CompassObservation, FlatInventoryObservation, TypeObservation


def test_merge_item_list_command_actions():
    assert ItemListCommandAction('test', ['A', 'B', 'C', 'D']) | ItemListCommandAction('test', ['E',
                                                                                                'F']) == ItemListCommandAction(
        'test', ['A', 'B', 'C', 'D', 'E', 'F'])


def test_merge_type_observation():
    type_obs_a = TypeObservation('test', ['none', 'A', 'B', 'C', 'D', 'other'])
    type_obs_b = TypeObservation('test', ['none', 'E', 'F', 'other'])
    type_obs_result = TypeObservation('test', ['none', 'A', 'B', 'C', 'D', 'E', 'F', 'other'])
    assert(type_obs_a | type_obs_b == type_obs_result)


def test_merge_flat_inventory_observation():
    assert FlatInventoryObservation(['stone', 'sandstone', 'lumber', 'wood', 'iron_bar']
                                    ) | FlatInventoryObservation(['ice', 'ice', 'ice', 'ice', 'ice', 'water']) == \
           FlatInventoryObservation(['stone', 'sandstone', 'lumber', 'wood', 'iron_bar', 'ice', 'water'])


def test_combine_compass_observations():
    assert CompassObservation() | CompassObservation() == CompassObservation()
