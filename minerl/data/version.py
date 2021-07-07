# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import os
import re
import glob

DATA_VERSION = 4
# Seems like this isn't used except for in visualizing a single trajectory?
# Perhaps we should remove it

FILE_PREFIX = "v{}_".format(DATA_VERSION)
VERSION_FILE_NAME = "VERSION"

# NOTE if you change ALLOWED_VERSIONS, update tests/test_dataset_version accordingly
ALLOWED_VERSIONS = (3, 4)


def get_version_violations(found_version, allowed=ALLOWED_VERSIONS):
    if found_version in allowed:
        return None
    if found_version < min(allowed):
        return "more"
    if found_version > max(allowed):
        return "less"


def assert_version(data_directory, version_fname=VERSION_FILE_NAME):
    version_file = os.path.join(data_directory, version_fname)

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
        version_violations = get_version_violations(current_version)
        if version_violations is not None:
            _raise_error(version_violations, data_directory)
        return current_version
    else:
        assert os.path.exists(data_directory), "MineRL data root: " \
                                               "{} not found!".format(data_directory)
        for exp in os.listdir(data_directory):
            if 'MineRL' in exp:
                exp_dir = os.path.join(data_directory, exp)
                for f in os.listdir(exp_dir):
                    return assert_prefix(os.path.join(exp_dir, f))


def assert_prefix(tail):
    """Asserts that a file name satisfies a certain prefix.
    
    Args:
        file_name (str): The file name to test.
    """
    assert os.path.exists(tail), "File {} does not exist.".format(tail)

    m = re.search('v([0-9]+?)_', tail)
    assert bool(m), "more"
    ver = int(m.group(1))

    version_violations = get_version_violations(ver)
    if version_violations is not None:
        _raise_error(version_violations)
    return ver


def _raise_error(exception, directory=None):
    comparison = str(exception)
    if comparison == "more":
        if directory:
            dir_str = "directory={}".format(directory)
        else:
            dir_str = os.environ['MINERL_DATA_ROOT']
        e = RuntimeError(
            "YOUR DATASET IS OUT OF DATE! The lowest supported version is v{} "
            "but yours is lower!\n\n"
            "\tRe-download the data using `minerl.data.download({})`".format(
                max(ALLOWED_VERSIONS), dir_str) +
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
