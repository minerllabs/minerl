# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

"""Launches a minecraft instance using the instance manager on a specified port.
"""

from minerl.env.malmo import InstanceManager, MinecraftInstance
import argparse
import logging
import time
import coloredlogs

coloredlogs.install(logging.DEBUG)


def parse_args():
    # Get a port to launch the instance on.
    parser = argparse.ArgumentParser(description='Launch a minecraft instance.')
    parser.add_argument('port', type=int, help='The port to launch the instance on.')
    parser.add_argument('--keep_alive',
                        action='store_true',
                        help='Keep the instance alive after the script exits.')
    args = parser.parse_args()
    return args.port, args.keep_alive


def main():
    port, keep_alive = parse_args()
    instance = MinecraftInstance(port)
    instance.launch(daemonize=True)
    if keep_alive:
        while True:
            time.sleep(10)


if __name__ == '__main__':
    main()
