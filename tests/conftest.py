import filelock
import pytest


@pytest.fixture(autouse=True)
def block_on_serial_mark(request):
    """Use file lock to force sequential run of tests decorated with
    `@pytest.mark.sequential` to avoid race-conditions with running tests in parallel.
    """
    # h/t: https://github.com/pytest-dev/pytest-xdist/issues/385#issuecomment-762670129

    # XXX: Could also have different file locks grouped by different pytest marks.
    #   IE using marker="sequential_{lock_group_name}"
    if request.node.get_closest_marker("serial"):
        with filelock.FileLock("tests/pytest_minerl_serial.lock"):
            yield
    else:
        yield
