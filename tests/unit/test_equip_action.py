from minerl.herobraine.hero import handlers
import pytest


def make_univ_hotbar(item_type: str, metadata: int):
    return dict(
        hotbar=11,
        slots=dict(gui={
            'type': 'class net.minecraft.inventory.ContainerPlayer',
            'slots': ["IGNORED_ELEMENT", dict(name=item_type, variant=metadata)],
        }))


def test_from_univ():
    def mk_handler():  # Need to generate new handler every time because from_universal is stateful.
        return handlers.EquipAction(["planks#0", "sandstone#12", "log", "none", "other"])
    assert mk_handler().from_universal(make_univ_hotbar("planks", 0)) == "planks#0"
    assert mk_handler().from_universal(make_univ_hotbar("planks", 1)) == "other"
    assert mk_handler().from_universal(make_univ_hotbar("sandstone", 0)) == "other"
    assert mk_handler().from_universal(make_univ_hotbar("sandstone", 12)) == "sandstone#12"
    assert mk_handler().from_universal(make_univ_hotbar("log", 0)) == "log"
    assert mk_handler().from_universal(make_univ_hotbar("log", 10)) == "log"
    assert mk_handler().from_universal(make_univ_hotbar("none", 0)) == "none"
    assert mk_handler().from_universal(make_univ_hotbar("other", 0)) == "other"


def test_from_univ_no_clobber_logs():
    def mk_handler():
        return handlers.EquipAction(["log", "none", "other"])
    assert mk_handler().from_universal(make_univ_hotbar("log", 0)) == "log"
    assert mk_handler().from_universal(make_univ_hotbar("log", 1)) == "log"
    assert mk_handler().from_universal(make_univ_hotbar("log2", 0)) == "other"
    assert mk_handler().from_universal(make_univ_hotbar("log2", 1)) == "other"


def test_from_univ_ignore_repeat():
    handler = handlers.EquipAction(["planks", "sandstone#12", "none", "other"])
    assert handler.from_universal(make_univ_hotbar("planks", 0)) == "planks"
    assert handler.from_universal(make_univ_hotbar("planks", 1)) == "none"
    assert handler.from_universal(make_univ_hotbar("planks", 2)) == "none"
    assert handler.from_universal(make_univ_hotbar("planks", 3)) == "none"
    assert handler.from_universal(make_univ_hotbar("log", 0)) == "other"
    assert handler.from_universal(make_univ_hotbar("log", 0)) == "none"
    assert handler.from_universal(make_univ_hotbar("planks", 3)) == "planks"
    assert handler.from_universal(make_univ_hotbar("sandstone", 12)) == "sandstone#12"
    assert handler.from_universal(make_univ_hotbar("sandstone", 12)) == "none"


def test_from_univ_other_repeats_selective_ignore():
    # Should ignore repeats of the same "other" item, but not changes between "other" items.
    handler = handlers.EquipAction(["planks", "sandstone#12", "none", "other"])
    assert handler.from_universal(make_univ_hotbar("sandstone", 0)) == "other"
    for _ in range(5):
        assert handler.from_universal(make_univ_hotbar("sandstone", 0)) == "none"
    for _ in range(5):
        assert handler.from_universal(make_univ_hotbar("sandstone", 1)) == "other"
        assert handler.from_universal(make_univ_hotbar("sandstone", 0)) == "other"

    assert handler.from_universal(make_univ_hotbar("planks", 0)) == "planks"
    assert handler.from_universal(make_univ_hotbar("stone_axe", 0)) == "other"
    assert handler.from_universal(make_univ_hotbar("stone_axe", 0)) == "none"
    assert handler.from_universal(make_univ_hotbar("stone_axe", 0)) == "none"


def test_to_hero_simple():
    handler = handlers.EquipAction(["planks#0", "none", "other"])
    with pytest.raises(ValueError, match=".*not found.*"):
        handler.to_hero("planks")
    assert handler.to_hero("planks#0") == "equip planks#0"
    assert handler.to_hero("none") == "equip none"
    assert handler.to_hero("other") == "equip other"


def test_to_hero():
    handler = handlers.EquipAction(["log#2", "planks", "sandstone#2", "none", "other"])
    for bad_key in ["planks#0", "log#3", "log2", "sandstone", "sandstone#3"]:
        with pytest.raises(ValueError, match=".*not found.*"):
            handler.to_hero(bad_key)

    assert handler.to_hero("none") == "equip none"
    assert handler.to_hero("other") == "equip other"
    assert handler.to_hero("log#2") == "equip log#2"
    assert handler.to_hero("sandstone#2") == "equip sandstone#2"
    assert handler.to_hero("planks") == "equip planks"
