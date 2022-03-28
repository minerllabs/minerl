# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import argparse
from minerl.env._multiagent import _MultiAgentEnv
from minerl.env.malmo import InstanceManager, MinecraftInstance, malmo_version
from minerl.env import comms
import os
import socket
import struct
import time

import logging
import coloredlogs

coloredlogs.install(logging.DEBUG)

logger = logging.getLogger(__name__)


def request_interactor(instance, ip):
    sock = get_socket(instance)
    comms.send_message(sock,
                       ("<MalmoEnv" + malmo_version + "/>").encode())

    comms.send_message(sock,
                       ("<Interact>" + ip + "</Interact>").encode())
    reply = comms.recv_message(sock)
    ok, = struct.unpack('!I', reply)
    if not ok:
        raise RuntimeError("Failed to start interactor")
    sock.close()


def get_socket(instance):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.settimeout(60)
    sock.connect((instance.host, instance.port))

    return sock


INTERACTOR_PORT = 31415


def run_interactor(ip, port, interactor_port=INTERACTOR_PORT):
    try:
        InstanceManager.add_existing_instance(interactor_port)
        instance = InstanceManager.get_instance(-1)
        print(instance)
    except AssertionError as e:
        logger.warning("No existing interactor found on port {}. Starting a new interactor.".format(interactor_port))
        instance = MinecraftInstance(interactor_port)
        instance.launch(daemonize=True)

    request_interactor(
        instance, '{}:{}'.format(ip, port)
    )


def parse_args():
    # Single argument for the port to launch the process.
    parser = argparse.ArgumentParser(description='Connect to an agent server.')
    parser.add_argument('port', type=int, default=8888,
                        help='The minecraft server port to connect to.')
    # ip default localhost
    parser.add_argument('-i', '--ip', default='127.0.0.1',
                        help='The ip to connect to.')
    parser.add_argument('--debug', action='store_true',
                        help='If this is set, then debug logging will be enabled.')
    return parser.parse_args()


if __name__ == '__main__':
    # TODO: Enable option of using existing mc instance
    # TODO: Enable spectator mode.
    opts = parse_args()
    if opts.debug:
        coloredlogs.install(logging.DEBUG)
    run_interactor(ip=opts.ip, port=opts.port)
