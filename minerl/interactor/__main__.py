import argparse
from minerl.env.malmo import InstanceManager, malmo_version
from minerl.env.core import MineRLEnv
from minerl.env import comms
import os
import socket
import struct
import time


def request_interactor(sock, ip):
   
    MineRLEnv._hello(sock)

    comms.send_message(sock,
        ("<Interact>" + ip + "</Interact>").encode())
    reply = comms.recv_message(sock)
    ok, = struct.unpack('!I', reply)
    if not ok:
        raise RuntimeError("Failed to start interactor")

def get_socket(instance):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.settimeout(60)
    sock.connect((instance.host, instance.port))
    MineRLEnv._hello(sock)

    return sock

def wait_while_running(sock):
    while True:
        time.sleep(1)
        try:
            MineRLEnv._hello(sock)
        except:
            return

def run_interactor(ip, port):
    instance = InstanceManager.get_instance(os.getpid())
    instance.launch()
    sock = get_socket(instance)
    request_interactor(
        sock, '{}:{}'.format(ip, port)
    )
    wait_while_running(sock)
    return
    


def parse_args():
    # Single argument for the port to launch the process.
    parser = argparse.ArgumentParser(description='Connect to an agent server.')
    parser.add_argument('port', type=int, default=8888,
                        help='The minecraft server port to connect to.')
    # ip default localhost
    parser.add_argument('-i', '--ip', default='127.0.0.1',
                        help='The ip to connect to.')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    # TODO: Enable option of using existing mc instance
    # TODO: Enable spectator mode.
    opts = parse_args()
    run_interactor(ip=opts.ip, port=opts.port)

