# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import os
import re
import glob

DATA_VERSION = 3
FILE_PREFIX = "v{}_".format(DATA_VERSION) # Seems like this isn't used?
VERSION_FILE_NAME = "VERSION"
ALLOWED_VERSIONS = (3, 4)
# TODO figure out logic for figuring out how to get the version we actually load in the `download` script
# Previously we had just used DATA_VERSION because it was forced to be identical with what was on disk
# Idea: have assert_version either raise an error, or else return the current on-disk version for `download` to use

def get_version_violations(found_version):
    if found_version in ALLOWED_VERSIONS:
        return None
    if found_version < min(ALLOWED_VERSIONS):
        return "more"
    if found_version > max(ALLOWED_VERSIONS):
        return "less"


def assert_version(data_directory):
    version_file = os.path.join(data_directory, VERSION_FILE_NAME)

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
    else:
        assert os.path.exists(data_directory), "MineRL data root: {} not found!".format(data_directory)
        for exp in os.listdir(data_directory):
            if 'MineRL' in exp:
                exp_dir = os.path.join(data_directory, exp)
                for f in os.listdir(exp_dir):
                    assert_prefix(os.path.join(exp_dir, f))



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


def _raise_error(exception, directory=None):
    comparison = str(exception)
    if comparison == "more":
        if directory:
            dir_str = "directory={}".format(directory)
        else:
            dir_str = os.environ['MINERL_DATA_ROOT']
        e = RuntimeError(
            "YOUR DATASET IS OUT OF DATE! The lowest supported version is v{} but yours is lower!\n\n"
            "\tRe-download the data using `minerl.data.download({})`".format(
                min(ALLOWED_VERSIONS), dir_str) +
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
