# ------------------------------------------------------------------------------------------------
# Copyright (c) 2018 Microsoft Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------
import os
import pathlib
import psutil
import subprocess
import threading
import socket
import atexit
import multiprocessing
import time
# from exceptions import NotImplementedError
from multiprocessing import process
from contextlib import contextmanager

import logging

logger = logging.getLogger(__name__)




class InstanceManager:
    """
    The static (singleton) hero instance manager. We avoid using the defualt Malmo
    instance management because it only allows one host.
    """
    MINECRAFT_DIR = os.path.join(os.path.dirname(__file__), 'Malmo', 'Minecraft') 
    MC_COMMAND = os.path.join(MINECRAFT_DIR, 'launchHero.sh')
    MAXINSTANCES = 10
    DEFAULT_IP = "127.0.0.1"
    _instance_pool = []
    X11_DIR = '/tmp/.X11-unix'
    headless = False
    managed = True

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
            inst.kill()

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
        port = 9000
        while cls._is_port_taken(port) or \
              cls._is_display_port_taken(port - 9000, cls.X11_DIR) or \
              cls._port_in_instance_pool(port):
            port += 1
        # print(port)
        return port


    @staticmethod
    def _process_watcher(parent_pid, child_pid):
        """
        On *nix systems (perhaps Windows) this is the central code for killing the child if the parent dies.
        """
        # Wait for processes to be launched
        time.sleep(1)
        try:
            child = psutil.Process(child_pid)
        except psutil.NoSuchProcess:
            child = None
        try:
            parent = psutil.Process(parent_pid)
        except psutil.NoSuchProcess:
            parent = None
        
        while True:
            try:
                time.sleep(0.1) # Sleep for a short time, and check if subprocesses needed to be killed.

                if not parent.is_running() or parent is None:
                    if not (child is None):
                        InstanceManager._reap_process_and_children(child)
                    return
                # Kill the watcher if the child is no longer running.
                # If you want to attempt to restart the child on failure, this
                # would be the location to do so.
                if not child.is_running():
                    return
            except KeyboardInterrupt:
                pass

    @staticmethod
    def _reap_process_and_children(process, timeout=3):
        "Tries hard to terminate and ultimately kill all the children of this process."
        def on_terminate(proc):
            logger.info("Minecraft process {} terminated with exit code {}".format(proc, proc.returncode))

        procs = process.children() + [process]
        # send SIGTERM
        for p in procs:
            try:
                p.terminate()
            except psutil.NoSuchProcess:
                pass
        gone, alive = psutil.wait_procs(procs, timeout=timeout, callback=on_terminate)
        if alive:
            # send SIGKILL
            for p in alive:
                logger.info("Minecraft process {} survived SIGTERM; trying SIGKILL".format(p.pid))
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            gone, alive = psutil.wait_procs(alive, timeout=timeout, callback=on_terminate)
            if alive:
                # give up
                for p in alive:
                    logger.info("Minecraft process {} survived SIGKILL; giving up".format(p.pid))



    class _Instance(object):
        """
        A subprocess wrapper which maintains a reference to a minecraft subprocess
        and also allows for stable closing and launching of such subprocesses 
        across different platforms.

        The Minecraft instance class works by launching two subprocesses:
        the Malmo subprocess, and a watcher subprocess with access to 
        the process IDs of both the parent process and the Malmo subprocess.
        If the parent process dies, it will kill the subprocess, and then itself.

        This scheme has a single failure point of the process dying before the watcher process is launched.
        """

        def __init__(self, port=None, existing=False):
            """
            Launches the subprocess.
            """
            self.running = False
            self.minecraft_process = None
            self.watcher_process = None
            self._port = None
            self._host = InstanceManager.DEFAULT_IP
            self.locked = False

            # Launch the instance!
            self.launch(port, existing)


        def launch(self, port=None, existing=False):
            if not existing:
                if not port:
                    port = InstanceManager._get_valid_port()

                    
                # 0. Get PID of launcher.
                parent_pid = os.getpid()
                # 1. Launch minecraft process.
                self.minecraft_process =  self._launch_minecraft(
                    port, 
                    InstanceManager.headless)
                # 2. Create a watcher process to ensure things get cleaned up
                self.watcher_process = self._launch_process_watcher(
                    parent_pid, self.minecraft_process.pid)
                
                # wait until Minecraft process has outputed "CLIENT enter state: DORMANT"
                while True:
                    line = self.minecraft_process.stdout.readline()
                    logger.debug(line)
                    if not line:
                        raise EOFError("Minecraft process finished unexpectedly")
                    if b"CLIENT enter state: DORMANT" in line:
                        break
                logger.info("Minecraft process ready")
                # supress entire output, otherwise the subprocess will block
                # NB! there will be still logs under Malmo/Minecraft/run/logs
                # FNULL = open(os.devnull, 'w')
                # launch a logger process
                def log_to_file():
                    if not os.path.exists(os.path.join('.', 'logs')):
                        os.makedirs((os.path.join('.', 'logs')))
                    
                    file_path = os.path.join('.', 'logs', 'minecraft_proc_{}.log'.format(port))

                    logger.info("Logging output of Minecraft to {}".format(file_path))
                    mine_log = open(file_path, 'wb+')
                    mine_log.truncate(0)
                    try:
                        while self.running:
                            line = self.minecraft_process.stdout.readline()
                            mine_log.write(line)
                            mine_log.flush()
                    finally:
                        mine_log.close()
                self._logger_thread = threading.Thread(target=log_to_file)
                self._logger_thread.setDaemon(True)
                self._logger_thread.start()


            else:
                assert port is not None, "No existing port specified."
            
            self._port = port

            self.running = True

            # Make a hook to kill
            atexit.register(lambda: self._destruct())

        def kill(self):
            """
            Kills the process (if it has been launched.)
            """
            self._destruct()
            pass

        @property
        def host(self):
            return self._host

        @property
        def port(self):
            return self._port

        ###########################
        ##### PRIVATE METHODS #####
        ###########################
        def _launch_minecraft(self, port, headless):
            """Launch Minecraft listening for malmoenv connections.
            Args:
                port:  the TCP port to listen on.
                installdir: the install dir name. Defaults to MalmoPlatform.
                Must be same as given (or defaulted) in download call if used.
                replaceable: whether or not to automatically restart Minecraft (default is false).
            Asserts:
                that the port specified is open.
            """
            replaceable = False

            launch_script = 'launchClient.sh'
            if os.name == 'nt':
                launch_script = 'launchClient.bat'

            launch_script = os.path.join(InstanceManager.MINECRAFT_DIR, launch_script)
            
            cmd = [launch_script, '-port', str(port), '-env']


            logger.info("Starting Minecraft process: " + str(cmd))
            # print(cmd)
            if replaceable:
                cmd.append('-replaceable')
            minecraft_process = subprocess.Popen(cmd,
                cwd=InstanceManager.MINECRAFT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                # use process group, see http://stackoverflow.com/a/4791612/18576
                preexec_fn=os.setsid
            )
            return minecraft_process

        def _launch_process_watcher(self, parent_pid, child_pid):
            """
            Launches the process watcher for the parent and miencraft process.
            """
            p = multiprocessing.Process(
                target=InstanceManager._process_watcher, args=(parent_pid, child_pid))
            # p.daemon = True
            p.start()
            return p

        def __del__(self):
            """
            On destruction of this instance kill the child.
            """
            self._destruct()
            pass

        def _destruct(self):
            """
            Do our best as the parent process to destruct and kill the child + watcher.
            """
            if self.running:
                # Wait for the process to start.
                time.sleep(1)
                # kill the minecraft process and its subprocesses
                try:
                    InstanceManager._reap_process_and_children(psutil.Process(self.minecraft_process.pid))
                except psutil.NoSuchProcess: 
                    pass

                # killall the watcher
                # try:
                self.watcher_process.terminate()

                if self in InstanceManager._instance_pool:
                    InstanceManager._instance_pool.remove(self)
                    self.release_lock()
                
                self.running = False
            pass

        
        def __repr__(self):
            return ("Malmo[proc={}, addr={}:{}, locked={}]".format(
                self.minecraft_process.pid if not self.existing else "EXISTING",
                self.ip,
                self.port,
                self.locked
            ))

        def _acquire_lock(self):
            self.locked = True

        def release_lock(self):
            self.locked = False
