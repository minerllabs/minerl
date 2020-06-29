"""
Calls the data viewer.
"""

import argparse
import logging
import random
import coloredlogs
import time
import numpy as np

import minerl
from minerl.viewer import get_parser
from minerl.viewer.trajectory_display_controller import TrajectoryDisplayController

coloredlogs.install(logging.DEBUG)
logger = logging.getLogger(__name__)




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
    main(get_parser().parse_args())
