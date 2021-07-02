from minerl.data.version import get_version_violations
import os

# Assumes current state where allowed versions are (3, 4)


def test_dataset_version():
    violations = get_version_violations(3)
    assert violations is None
    violations = get_version_violations(4)
    assert violations is None
    violations = get_version_violations(2)
    assert violations == "more"
    violations = get_version_violations(5)
    assert violations == "less"
