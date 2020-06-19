"""
Calls the data viewer.
"""

import argparse
import logging
import random
import coloredlogs
import time
import numpy as np

from minerl.viewer.trajectory_display_controller import TrajectoryDisplayController

coloredlogs.install(logging.DEBUG)
logger = logging.getLogger(__name__)

import minerl
from minerl.data import FILE_PREFIX

_DOC_TRAJ_NAME = "{}absolute_zucchini_basilisk-13_36805-50154".format(FILE_PREFIX)


def parse_args():
    parser = argparse.ArgumentParser("python3 -m minerl.viewer")
    parser.add_argument("environment", type=str,
                        help='The MineRL environment to visualize. e.g. MineRLObtainDiamondDense-v0')

    parser.add_argument("stream_name", type=str, nargs='?', default=None,
                        help="(optional) The name of the trajectory to visualize. "
                             "e.g. {}."
                             "".format(_DOC_TRAJ_NAME))

    return parser.parse_args()


def main(opts):
    logger.info("Welcome to the MineRL Stream viewer! \n")

    logger.info("Building data pipeline for {}".format(opts.environment))
    data = minerl.data.make(opts.environment)

    # for _ in data.seq_iter( 1, -1, None, None, include_metadata=True):
    #     print(_[-1])
    #     pass
    if opts.stream_name is None:
        trajs = data.get_trajectory_names()
        opts.stream_name = random.choice(trajs)

    logger.info("Loading data for {}...".format(opts.stream_name))
    data_frames = list(data.load_data(opts.stream_name, include_metadata=True))
    meta = data_frames[0][-1]
    logger.info("Data loading complete!".format(opts.stream_name))
    logger.info("META DATA: {}".format(meta))

    trajectory_display_controller = TrajectoryDisplayController(
        data_frames,
        header=opts.environment,
        subtext=opts.stream_name,
        vector_display='VectorObf' in opts.environment
    )
    trajectory_display_controller.run()


if __name__ == '__main__':
    main(parse_args())
