import os
import re
import glob

DATA_VERSION = 3
FILE_PREFIX = "v{}_".format(DATA_VERSION)
VERSION_FILE_NAME = "VERSION"


def assert_version(data_directory):
    version_file = os.path.join(data_directory, VERSION_FILE_NAME)

    try:
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                try:
                    txt = int(f.read())
                except FileNotFoundError:
                    raise AssertionError("less")
                except Exception as e:
                    print('VERSION number not found in data folder')
                    raise e
                current_version = txt

            assert DATA_VERSION <= txt, "more"
            assert DATA_VERSION >= txt, "less"
        else:
            assert os.path.exists(data_directory), "MineRL data root: {} not found!".format(data_directory)
            for exp in os.listdir(data_directory):
                if 'MineRL' in exp:
                    exp_dir = os.path.join(data_directory, exp)
                    for f in os.listdir(exp_dir):
                        assert_prefix(os.path.join(exp_dir, f))

    except AssertionError as e:
        _raise_error(e, data_directory)


def assert_prefix(tail):
    """Asserts that a file name satifies a certain prefix.
    
    Args:
        file_name (str): The file name to test.
    """
    try:
        assert os.path.exists(tail), "File {} does not exist.".format(tail)

        m = re.search('v([0-9]+?)_', tail)
        assert bool(m), "more"
        ver = int(m.group(1))

        assert DATA_VERSION <= ver, "more"
        assert DATA_VERSION >= ver, "less"

    except AssertionError as e:
        _raise_error(e)


def _raise_error(exception, directory=None):
    comparison = str(exception)
    if comparison == "more":
        if directory:
            dir_str = "directory={}".format(directory)
        else:
            dir_str = os.environ['MINERL_DATA_ROOT']
        e = RuntimeError(
            "YOUR DATASET IS OUT OF DATE! The latest is on version v{} but yours is lower!\n\n"
            "\tRe-download the data using `minerl.data.download({})`".format(
                DATA_VERSION, dir_str) +
            "\n\n CONFIGURED MINERL_DATA_DIR = {}".format(dir_str))
        e.comparison = comparison
        raise e
    elif comparison == "less":
        e = RuntimeError(
            "YOUR MINERL PACKAGE IS OUT OF DATE! \n\n\tPlease upgrade with `pip3 install --upgrade minerl`")
        e.comparison = comparison
        raise e
    else:
        raise exception
