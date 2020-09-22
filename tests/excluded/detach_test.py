import argparse
import logging
import os
import shutil
import signal
import subprocess
import sys
import time

import psutil

import minerl
from daemoniker import daemonize


def launch():
    print("parent launchin daemon process.!")
    p = psutil.Popen([
        'python', 'detach_test.py', 'daemon'])
    p.wait()


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'daemon':

        daemonize('pid.pid')

        print("daemon", os.getpid(), os.getppid())
        time.sleep(1)
        print("daemon I am detached :)")
        for _ in range(20):
            time.sleep(1)
            print("daemon guy waiting.")
        print("daemon closing.")
        exit()
    else:
        launch()
        time.sleep(10)
        print("parent closing!")
