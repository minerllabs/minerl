# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

"""A module for viewing individual streams from the dataset!

To use:
```
    python3 -m minerl.viewer <environment name> <trajectory name>
```
"""
import argparse

from minerl.data import FILE_PREFIX

_DOC_TRAJ_NAME = "{}absolute_zucchini_basilisk-13_36805-50154".format(FILE_PREFIX)


def get_parser():
    parser = argparse.ArgumentParser("python3 -m minerl.viewer")
    parser.add_argument("environment", type=str,
                        help='The MineRL environment to visualize. e.g. MineRLObtainDiamondDense-v0')

    parser.add_argument("stream_name", type=str, nargs='?', default=None,
                        help="(optional) The name of the trajectory to visualize. "
                             "e.g. {}."
                             "".format(_DOC_TRAJ_NAME))

    return parser
