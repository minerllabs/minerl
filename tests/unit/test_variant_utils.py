import functools

import pytest

from minerl.herobraine.hero.handlers import util


def test_error_on_malformed_ok():
    """Test non-error cases."""
    f = util.error_on_malformed_item_list
    f([], [])
    f(["planks"], [])
    f(["planks#2"], [])
    f(["planks#15", "planks#0"], [])
    f(["planks#15", "planks#0", "air#2"], ["other"])
    f(["a", "b", "c"], ["a", "b", "c"])
    f(["a", "b", "c#0", "c#2", "d", "c#3"], ["a", "b"])


def test_error_on_malformed_error():
    """Test error cases."""
    f = util.error_on_malformed_item_list
    with pytest.raises(ValueError, match="Duplicate item.*"):
        f(["a", "a"], [])

    with pytest.raises(ValueError, match="Duplicate item.*"):
        f(["a#0", "a#0"], ["b"])

    with pytest.raises(ValueError, match="Duplicate item.*"):
        f(["a#0", "b", "c", "d", "a#0"], ["b"])

    with pytest.raises(ValueError, match=".*overlap"):
        f(["a", "a#0"], [])

    with pytest.raises(ValueError, match=".*overlap"):
        f(["b#2", "a#0", "a"], [])

    with pytest.raises(ValueError, match=".*metadata.*special.*"):
        f(["a#0"], ["a"])

    with pytest.raises(ValueError, match=".*metadata.*special.*"):
        f(["a", "d#0", "d#2", "b#3", "d#4"], ["a", "b"])


def test_get_unique_matching_item_list_id_basic():
    f = util.get_unique_matching_item_list_id

    assert f(item_list=[], item_type="a", metadata=1) is None

    for metadata in range(10):
        assert f(item_list=["a"], item_type="a", metadata=metadata) == "a"
        assert f(item_list=["a"], item_type="b", metadata=metadata) is None

    assert f(item_list=["a", "b#1", "b#2"], item_type="b", metadata=0) is None
    assert f(item_list=["a", "b#1", "b#2"], item_type="b", metadata=1) == "b#1"
    assert f(item_list=["a", "b#1", "b#2"], item_type="b", metadata=2) == "b#2"


def test_get_unique_matching_item_list_id_clobber_logs():
    f = util.get_unique_matching_item_list_id

    # clobber_logs = True case -- log2 should clobber to log.
    for metadata in range(10):
        assert f(item_list=["log"], item_type="log", metadata=metadata, clobber_logs=True) == "log"
        assert f(item_list=["log"], item_type="log2", metadata=metadata, clobber_logs=True) == "log"

    # clobber_logs = False -- log2 should not clobber to log.
    for metadata in range(10):
        assert f(item_list=["log"], item_type="log", metadata=metadata, clobber_logs=False) == "log"
        assert f(item_list=["log"], item_type="log2", metadata=metadata, clobber_logs=False) is None

    # Tests for cases that are unaffected by clobber_logs setting.
    for clobber_logs in [True, False]:
        g = functools.partial(f, clobber_logs=clobber_logs)
        assert g(item_list=[], item_type="log", metadata=0) is None
        assert g(item_list=[], item_type="log2", metadata=0) is None

        assert g(item_list=["log#0"], item_type="log", metadata=0) == "log#0"

        # clobber_logs is ignored if any log with metadata or log2 is in the item list.
        assert g(item_list=["log#0"], item_type="log2", metadata=0) is None
        assert g(item_list=["log", "log2"], item_type="log2", metadata=0) is "log2"
        assert g(item_list=["log#0", "log#1", "log2#7"], item_type="log2", metadata=0) is None
        assert g(item_list=["log#0", "log#1", "log2#7"], item_type="log2", metadata=7) == "log2#7"
