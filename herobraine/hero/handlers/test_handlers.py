
# Tests merging two item list commands
from herobraine.hero.handlers.actionable import ItemListCommandAction
from herobraine.hero.handlers.observables import CompassObservation, FlatInventoryObservation, TypeObservation


def test_merge_item_list_command_actions():
    assert ItemListCommandAction('test', ['A', 'B', 'C', 'D']) | ItemListCommandAction('test', ['E', 'F']) == ItemListCommandAction('test', ['A', 'B', 'C', 'D', 'E', 'F'])

def test_merge_type_observation():
    assert TypeObservation('test', ['none', 'A', 'B', 'C', 'D', 'other']
    ) | TypeObservation('test', ['none', 'E', 'F', 'other']) == TypeObservation('test',
     ['none', 'A', 'B', 'C', 'D', 'E', 'F', 'other'])




def test_merge_flat_inventory_observation():
    assert FlatInventoryObservation(['stone', 'sandstone', 'lumber', 'wood', 'iron_bar']
                                    ) | FlatInventoryObservation(['ice', 'ice', 'ice', 'ice', 'ice', 'water']) == \
           FlatInventoryObservation(['stone', 'sandstone', 'lumber', 'wood', 'iron_bar', 'ice', 'water'])


def test_combine_compass_observations():
    assert CompassObservation() | CompassObservation() == CompassObservation()