# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

"""
Calls the data viewer.
"""

import logging
import random
import coloredlogs

import minerl
from minerl.viewer import get_parser
from minerl.viewer.trajectory_display_controller import TrajectoryDisplayController

coloredlogs.install(logging.DEBUG)
logger = logging.getLogger(__name__)


def main(env_name: str, stream_name: str):
    logger.info("Welcome to the MineRL Stream viewer! \n")

    logger.info(f"Building data pipeline for {env_name}")
    data = minerl.data.make(env_name)

    # for _ in data.seq_iter( 1, -1, None, None, include_metadata=True):
    #     print(_[-1])
    #     pass
    if stream_name is None:
        trajs = data.get_trajectory_names()
        stream_name = random.choice(trajs)

    logger.info(f"Loading data for {stream_name}...")
    data_frames = list(data.load_data(stream_name, include_metadata=True))
    meta = data_frames[0][-1]
    logger.info("Data loading complete!")
    logger.info(f"META DATA: {meta}")

    trajectory_display_controller = TrajectoryDisplayController(
        data_frames,
        header=env_name,
        subtext=stream_name,
        vector_display='VectorObf' in env_name
    )
    trajectory_display_controller.run()


if __name__ == '__main__':
    args = get_parser().parse_args()
    main(env_name=args.environment, stream_name=args.stream_name)
