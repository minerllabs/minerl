from minerl.herobraine.hero.handlers.agent.observations import equipped_item


def make_hero_obs(item_type: str, metadata: int):
    return dict(equipped_items=dict(mainhand=dict(
        type=item_type,
        metadata=metadata,
    )))


def test_from_hero():
    handler = equipped_item._ItemIDObservation(
        ["mainhand"],
        items=["none", "other", "planks#0", "planks#1"],
        _default="none", _other="other",
    )

    assert handler.from_hero(make_hero_obs("none", 0)) == "none"
    assert handler.from_hero(make_hero_obs("other", 0)) == "other"
    assert handler.from_hero(make_hero_obs("planks", 0)) == "planks#0"
    assert handler.from_hero(make_hero_obs("planks", 1)) == "planks#1"
    assert handler.from_hero(make_hero_obs("planks", 15)) == "other"

    handler = equipped_item._ItemIDObservation(
        ["mainhand"],
        items=["none", "other", "sandstone"],
        _default="none", _other="other",
    )
    for metadata in range(10):
        assert handler.from_hero(make_hero_obs("sandstone", metadata)) == "sandstone"


def make_univ_hotbar(item_type: str, metadata: int):
    return dict(
        hotbar=11,
        slots=dict(gui={
            'type': 'class net.minecraft.inventory.ContainerPlayer',
            'slots': ["IGNORED_ELEMENT", dict(name=item_type, variant=metadata)],
        }))


def test_from_univ():
    handler = equipped_item._ItemIDObservation(
        ["mainhand"],
        items=["none", "other", "planks#0", "planks#1"],
        _default="none", _other="other",
    )
    assert handler.from_universal(make_univ_hotbar(item_type="air", metadata=0)) == "none"
    assert handler.from_universal(make_univ_hotbar(item_type="log", metadata=0)) == "other"
    assert handler.from_universal(make_univ_hotbar(item_type="planks", metadata=0)) == "planks#0"
    assert handler.from_universal(make_univ_hotbar(item_type="planks", metadata=1)) == "planks#1"
    assert handler.from_universal(make_univ_hotbar(item_type="planks", metadata=2)) == "other"

    handler = equipped_item._ItemIDObservation(
        ["mainhand"],
        items=["none", "other", "sandstone"],
        _default="none", _other="other",
    )
    assert handler.from_universal(make_univ_hotbar(item_type="air", metadata=0)) == "none"
    assert handler.from_universal(make_univ_hotbar(item_type="log", metadata=0)) == "other"
    assert handler.from_universal(make_univ_hotbar(item_type="planks", metadata=0)) == "other"
    assert handler.from_universal(make_univ_hotbar(item_type="sandstone", metadata=2)
                                  ) == "sandstone"
