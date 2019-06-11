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
import atexit
import functools
import locale
import logging
import multiprocessing
import os
import pathlib
import socket
import struct
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
# from exceptions import NotImplementedError
from multiprocessing import process

import psutil
from minerl.env import comms

logger = logging.getLogger(__name__)

malmo_version = "0.37.0"

class InstanceManager:
    """The Minecraft instance manager library. The instance manager can be used to allocate and safely terminate 
    existing Malmo instances for training agents. 
    
    Note: This object never needs to be explicitly invoked by the user of the MineRL library as the creation of
    one of the several MineRL environments will automatically query the InstanceManager to create a new instance.

    Note: In future versions of MineRL the instance manager will become its own daemon process which provides
    instance allocation capability using remote procedure calls.
    """
    MINECRAFT_DIR = os.path.join(os.path.dirname(__file__), 'Malmo', 'Minecraft') 
    MAXINSTANCES = 10
    DEFAULT_IP = "localhost"
    _instance_pool = []
    ninstances = 0
    X11_DIR = '/tmp/.X11-unix'
    headless = False
    managed = True

    @classmethod
    @contextmanager
    def get_instance(cls):
        """
        Gets an instance from the instance manager. This method is a context manager
        and therefore when the context is entered the method yields a InstanceManager._Instance
        object which contains the allocated port and host for the given instance that was created.

        Yields:
            The allocated InstanceManager._Instance object.
        
        Raises:
            RuntimeError: No available instances or the maximum number of allocated instances reached.
            RuntimeError: No available instances and automatic allocation of isntances is off.
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
                cls.ninstances += 1
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
        instance = InstanceManager._Instance(port=port, existing=True)
        cls._instance_pool.append(instance)
        cls.ninstances += 1
        return instance


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
        return False

    @classmethod
    def _port_in_instance_pool(cls, port):
        # Ideally, this should be covered by other cases, but there may be delay
        # in when the ports get "used"
        return port in [instance.port for instance in cls._instance_pool]

    @classmethod
    def _get_valid_port(cls):
        port = (cls.ninstances  % 5000) + 9000
        while cls._is_port_taken(port) or \
              cls._is_display_port_taken(port - 9000, cls.X11_DIR) or \
              cls._port_in_instance_pool(port):
            port += 1
        return port


    @staticmethod
    def _process_watcher(parent_pid, child_pid, child_host, child_port):
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
    def _reap_process_and_children(process, timeout=5):
        "Tries hard to terminate and ultimately kill all the children of this process."
        def on_terminate(proc):
            logger.info("Minecraft process {} terminated with exit code {}".format(proc, proc.returncode))

        procs = process.children() + [process]
        
        # send SIGTERM
        for p in procs:
            try:
                try:
                    import signal
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                except:
                    pass
                p.kill()
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
            self.existing = existing

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
                    parent_pid, self.minecraft_process.pid, self.host, port)
                
                # wait until Minecraft process has outputed "CLIENT enter state: DORMANT"
                lines = []
                client_ready = False
                server_ready = False
                while True:
                    line = self.minecraft_process.stdout.readline().decode('utf-8')

                    # Check for failures and print useful messages!
                    _check_for_launch_errors(line)

                    lines.append(line)
                    logger.debug("\n".join(line.split("\n")[:-1]))
                    if not line:
                        raise EOFError("Minecraft process finished unexpectedly")
                    client_ready =  "CLIENT enter state: DORMANT" in line
                    server_ready =  "SERVER enter state: DORMANT" in line
                    if  client_ready:
                        break


                logger.info("Minecraft process ready")
                # supress entire output, otherwise the subprocess will block
                # NB! there will be still logs under Malmo/Minecraft/run/logs
                # FNULL = open(os.devnull, 'w')
                # launch a logger process
                def log_to_file(logdir):
                    if not os.path.exists(os.path.join(logdir, 'logs')):
                        os.makedirs((os.path.join(logdir, 'logs')))

                    file_path = os.path.join(logdir, 'logs', 'minecraft_proc_{}.log'.format(port))

                    logger.info("Logging output of Minecraft to {}".format(file_path))
                    mine_log = open(file_path, 'wb+')
                    mine_log.truncate(0)
                    mine_log_encoding = 'utf-8'
                    try:
                        while self.running:
                            line = self.minecraft_process.stdout.readline()
                            try:
                                linestr = line.decode(mine_log_encoding)
                            except UnicodeDecodeError:
                                mine_log_encoding = locale.getpreferredencoding(False)
                                logger.error("UnicodeDecodeError, switching to default encoding")
                                linestr = line.decode(mine_log_encoding)
                            linestr = "\n".join(linestr.split("\n")[:-1])
                            if 'STDERR' in linestr or 'ERROR' in linestr:
                                # Opportune place to suppress harmless MC errors.
                                if not ('hitResult' in linestr):
                                    logger.error(linestr)
                            if 'LOGTOPY' in linestr:
                                logger.info(linestr)
                            mine_log.write(line)
                            mine_log.flush()
                    finally:
                        mine_log.close()
                logdir = os.environ.get('MALMO_MINECRAFT_OUTPUT_LOGDIR', '.')
                self._logger_thread = threading.Thread(target=functools.partial(log_to_file, logdir=logdir))
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
            preexec_fn = os.setsid if 'linux' in str(sys.platform) else None
            # print(preexec_fn)
            minecraft_process = subprocess.Popen(cmd,
                cwd=InstanceManager.MINECRAFT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                # use process group, see http://stackoverflow.com/a/4791612/18576
                preexec_fn=preexec_fn
            )
            return minecraft_process

        def _launch_process_watcher(self, parent_pid, child_pid, child_host, child_port):
            """
            Launches the process watcher for the parent and miencraft process.
            """
            p = multiprocessing.Process(
                target=InstanceManager._process_watcher, args=(parent_pid, child_pid, child_host, child_port))
            # p.daemon = True
            p.start()
            return p

        @staticmethod
        def _kill_minecraft_via_malmoenv(host, port):
            """Use carefully to cause the Minecraft service to exit (and hopefully restart).
            """
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((host, port))
                comms.send_message(sock, ("<MalmoEnv" + malmo_version + "/>").encode())

                comms.send_message(sock, ("<Exit>NOW</Exit>").encode())
                reply = comms.recv_message(sock)
                ok, = struct.unpack('!I', reply)
                sock.close()
                return ok == 1
            except Exception as e:
                print(e)
                logger.error("Attempted to send kill command to minecraft process and failed.")
                return False

        def __del__(self):
            """
            On destruction of this instance kill the child.
            """
            self._destruct()

        def _destruct(self):
            """
            Do our best as the parent process to destruct and kill the child + watcher.
            """
            if self.running and not self.existing:
                # Wait for the process to start.
                time.sleep(1)
                # kill the minecraft process and its subprocesses


                if self._kill_minecraft_via_malmoenv(self.host, self.port):
                    # Let the miencraft process term on its own terms.
                    time.sleep(2)

                # Now lets try and end the process if anything is laying around
                try:
                    InstanceManager._reap_process_and_children(psutil.Process(self.minecraft_process.pid))
                except psutil.NoSuchProcess: 
                    pass

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


def _check_for_launch_errors(line):
    if "at org.lwjgl.opengl.Display.<clinit>(Display.java:138)" in line:
        raise  RuntimeError(
            "ERROR! MineRL could not detect an X Server, Monitor, or Virtual Monitor! "
            "Currently minerl only supports environment rendering in headed environments (servers with monitors attached)."
            "\n"
            "\n"
            "In order to run minerl environments without a head use a software renderer such as 'xvfb':"
            "\n\txvfb-run python3 <your_script.py>"
            "\n"
            "If you're receiving this error and there is a monitor attached, make sure your current display"
            "variable is set correctly: "
            "\n\t DISPLAY=:0 python3 <your_script.py>"
            "\n"
            "If none of these steps work, please complain in the discord!"
        )

