import logging
import os
import shlex
import signal
import socket
import subprocess
import time
from contextlib import contextmanager

import MalmoPython

# Todo: Fix instance manager spawnign up a lot of instances bug.

logger = logging.getLogger(__name__)


class InstanceManager:
    """
    The static (singleton) hero instance manager. We avoid using the defualt Malmo
    instance management because it only allows one host.
    """
    MINECRAFT_DIR = os.path.join("/minerl.herobraine", "scripts")
    MC_COMMAND = os.path.join(MINECRAFT_DIR, 'launchHero.sh')
    MAXINSTANCES = 10
    DEFAULT_IP = "127.0.0.1"
    _instance_pool = []
    X11_DIR = '/tmp/.X11-unix'
    headless = False
    managed = False

    @classmethod
    @contextmanager
    def get_instance(cls):
        """
        Gets an instance
        :return: The available instances port and IP.
        """
        # Find an available instance.
        for inst in cls._instance_pool:
            if not inst.locked:
                inst._acquire_lock()

                yield inst

                inst.release_lock()
                return
        # Otherwise make a new instance if possible
        if cls.managed:
            if len(cls._instance_pool) < cls.MAXINSTANCES:
                inst = cls._Instance(cls._get_valid_port())
                cls._instance_pool.append(inst)
                inst._acquire_lock()
                yield inst
                inst.release_lock()
                return
            else:
                raise RuntimeError("No available instances and max instances reached! :O :O")
        else:
            raise RuntimeError("No available instances and managed flag is off")

    @classmethod
    def shutdown(cls):
        # Iterate over a copy of instance_pool because _stop removes from list
        # This is more time/memory intensive, but allows us to have a modular
        # stop function
        for inst in cls._instance_pool[:]:
            inst.release_lock()
            inst._stop()

    @classmethod
    @contextmanager
    def allocate_pool(cls, num):
        for _ in range(num):
            inst = cls._Instance(cls._get_valid_port())
            cls._instance_pool.append(inst)
        yield None
        cls.shutdown()

    @classmethod
    def add_existing_instance(cls, port):
        assert cls._is_port_taken(port), "No Malmo mod utilizing the port specified."
        cls._instance_pool.append(InstanceManager._Instance(port=port, existing=True))

    class _Instance:
        def __init__(self, port=None, existing=False):
            self.existing = existing

            if not existing:
                if not port:
                    port = InstanceManager._get_valid_port()
                cmd = InstanceManager.MC_COMMAND
                if InstanceManager.headless:
                    cmd += " -headless "
                cmd += " -port " + str(port)
                logger.info("Starting Minecraft process: " + cmd)

                args = shlex.split(cmd)
                proc = subprocess.Popen(args, cwd=InstanceManager.MINECRAFT_DIR,
                                        # pipe entire output
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        # use process group, see http://stackoverflow.com/a/4791612/18576
                                        preexec_fn=os.setsid)
                # wait until Minecraft process has outputed "CLIENT enter state: DORMANT"
                while True:
                    line = proc.stdout.readline()
                    logger.debug(line)
                    if not line:
                        raise EOFError("Minecraft process finished unexpectedly")
                    if b"CLIENT enter state: DORMANT" in line:
                        break
                logger.info("Minecraft process ready")
                # supress entire output, otherwise the subprocess will block
                # NB! there will be still logs under Malmo/Minecraft/run/logs
                # FNULL = open(os.devnull, 'w')
                FMINE = open('./minecraft.log', 'w')
                proc.stdout = FMINE
                self.proc = proc
            else:
                assert port is not None, "No existing port specified."

            self.ip = InstanceManager.DEFAULT_IP
            self.port = port
            self.existing = existing
            self.locked = False


            # Creating client pool.
            logger.info("Creating client pool for {}".format(self))
            self.client_pool = MalmoPython.ClientPool()
            self.client_pool.add(MalmoPython.ClientInfo(self.ip, self.port))

            # Set the lock.


        def _stop(self):
            if not self.existing:
                # Kill the VNC server if we started it
                cmd = "/opt/TurboVNC/bin/vncserver "
                cmd += "-kill :" + str(self.port - 10000)
                args = shlex.split(cmd)
                subprocess.Popen(args)

                # send SIGTERM to entire process group, see http://stackoverflow.com/a/4791612/18576
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
                logger.info("Minecraft process terminated")
                
            if self in InstanceManager._instance_pool:
                InstanceManager._instance_pool.remove(self)
                self.release_lock()

            self.terminated = True

        def _acquire_lock(self):
            self.locked = True

        def release_lock(self):
            self.locked = False

        def __repr__(self):
            return ("Malmo[proc={}, addr={}:{}, locked={}]".format(
                self.proc.pid if not self.existing else "EXISTING",
                self.ip,
                self.port,
                self.locked
            ))

    @staticmethod
    def _is_port_taken(port, address='0.0.0.0'):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.bind((address, port))
            taken = False
        except socket.error as e:
            if e.errno in [98, 10048]:
                taken = True
            else:
                raise e

        s.close()
        return taken

    @staticmethod
    def _is_display_port_taken(port, x11_path):
        # Returns a display port that is unused
        xs = os.listdir(x11_path)
        return ('X' + str(port)) in xs

    @classmethod
    def _port_in_instance_pool(cls, port):
        # Ideally, this should be covered by other cases, but there may be delay
        # in when the ports get "used"
        return port in [instance.port for instance in cls._instance_pool]

    @classmethod
    def _get_valid_port(cls):
        port = 10000
        while cls._is_port_taken(port) or \
              cls._is_display_port_taken(port - 10000, cls.X11_DIR) or \
              cls._port_in_instance_pool(port):
            port += 1
        return port
