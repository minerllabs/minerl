import pytest

from minerl.herobraine.hero import handlers


def test_init():
    handlers.FlatInventoryObservation([])
    handlers.FlatInventoryObservation(["planks"])
    handlers.FlatInventoryObservation(["planks#2", "other"])
    handlers.FlatInventoryObservation(["planks#2", "planks#6", "a", "b#0", "other"])
    with pytest.raises(ValueError):
        handlers.FlatInventoryObservation(["planks#2", "other#3"])
    with pytest.raises(ValueError, match=".*overlap.*"):
        handlers.FlatInventoryObservation(["planks#2", "planks"])


def make_inventory_obs(inv_spec):
    """
    make_inventory([("a#2", 3), ("b", 1)])
        ==> dict(inventory=[
                dict(type=a, metadata=2, quantity=2),
                dict(type=b, metadata=0, quantity=1),
                ])
    """
    inventory = []
    for item_id, quantity in inv_spec:
        item_type, metadata = item_id.split('#')
        inventory.append(dict(item_type=item_type, metadata=metadata, quantity=quantity))
    return {'inventory': inventory}


def test_from_hero_simple_quantity_change():
    handler = handlers.FlatInventoryObservation(["a", "other"])

    for quantity in range(10):
        obs = handler.from_hero(dict(
            inventory=[
                dict(type='a', quantity=quantity, metadata=0),
            ],
        ))
        assert obs == {'a': quantity, 'other': 0}


def test_from_hero_simple_quantity_change_mixed_metadata():
    # Like the previous test, except we also test that we are boxing metadata
    # into the right bins in the "specific metadata" and "nonspecific metadata" (flat)
    # cases.
    handler = handlers.FlatInventoryObservation(["a", "b#0", "b#1", "b#2", "other"])
    handler_flat = handlers.FlatInventoryObservation(["a", "b", "other"])

    for quantity_a in range(10):
        for quantity_b_0 in range(10):
            for quantity_b_1 in range(10):
                hero_obs = dict(
                    inventory=[
                        dict(type='a', quantity=quantity_a, metadata=0),

                        dict(type='b', quantity=quantity_b_0, metadata=0),

                        # Should add together these two stacks.
                        dict(type='b', quantity=quantity_b_1, metadata=1),
                        dict(type='b', quantity=quantity_b_1, metadata=1),

                        # Should be grouped together as other
                        dict(type='apple', quantity=quantity_a, metadata=0),
                        dict(type='banana', quantity=quantity_b_0, metadata=0),
                        dict(type='banana', quantity=quantity_b_1, metadata=1),
                    ],
                )

                obs = handler.from_hero(hero_obs)
                assert obs == {
                    'a': quantity_a,
                    'b#0': quantity_b_0,
                    'b#1': quantity_b_1 * 2,
                    'b#2': 0,
                    'other': quantity_a
                             + quantity_b_0
                             + quantity_b_1,
                }

                obs_flat = handler_flat.from_hero(hero_obs)
                assert obs_flat == {
                    'a': quantity_a,
                    'b': quantity_b_0 + quantity_b_1 * 2,
                    'other': quantity_a
                             + quantity_b_0
                             + quantity_b_1,
                }


def make_univ_obs(slots: list) -> dict:
    return dict(slots=dict(gui={
        'type': 'class net.minecraft.inventory.ContainerPlayer',
        'slots': ["IGNORED_ELEMENT"] + slots,
    }))


def test_from_universal_blank():
    handler = handlers.FlatInventoryObservation([])
    assert handler.from_universal(make_univ_obs([])) == {}
    assert handler.from_universal(
        make_univ_obs([dict(name="planks", variant=0, count=5)])) == {}


def test_from_universal_logs_no_clobber():
    handler = handlers.FlatInventoryObservation(["log", "log2#0", "log2#1"])
    assert handler.from_universal(make_univ_obs([])) == {
        "log": 0,
        "log2#0": 0,
        "log2#1": 0,
    }
    univ_obs = make_univ_obs([
        dict(name="log", variant=0, count=5),
        dict(name="log", variant=0, count=5),
        dict(name="log", variant=1, count=5),
        dict(name="log2", variant=0, count=6),
        dict(name="log2", variant=1, count=7),
    ])
    assert handler.from_universal(univ_obs) == {
        "log": 15,
        "log2#0": 6,
        "log2#1": 7,
    }


def test_from_universal_logs_clobber():
    handler = handlers.FlatInventoryObservation(["log", "planks"])
    univ_obs = make_univ_obs([
        dict(name="log", variant=0, count=5),
        dict(name="log", variant=1, count=5),
        dict(name="log2", variant=0, count=5),
        dict(name="log2", variant=1, count=5),
    ])
    assert handler.from_universal(univ_obs) == {
        "log": 20,
        "planks": 0,
    }


def test_from_universal_logs_complex():
    handler = handlers.FlatInventoryObservation(
        ["log#0", "planks", "sandstone#1", "sandstone#2", "air"])
    univ_obs = make_univ_obs([
        dict(name='log', variant=0, count=5),
        dict(name='log', variant=1, count=5),
        dict(name='log2', variant=0, count=7),
        dict(name='planks', variant=0, count=1),
        dict(name='planks', variant=1, count=2),
        dict(name='sandstone', variant=0, count=1),
        dict(name='sandstone', variant=1, count=2),
        dict(name='sandstone', variant=2, count=3),
        dict(name='sandstone', variant=2, count=3),
        dict(name='air', variant=0, count=10),
        {}
    ])
    assert handler.from_universal(univ_obs) == {
        'log#0': 5,
        'planks': 3,
        'sandstone#1': 2,
        'sandstone#2': 6,
        'air': 2,  # Special case -- counts number of air slots instead of total quantity.
    }
