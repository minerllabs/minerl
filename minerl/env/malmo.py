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
import traceback
import pathlib 
import Pyro4.core
import argparse
from enum import IntEnum
 
import shutil
import socket
import struct
import collections
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
# from exceptions import NotImplementedError
from multiprocessing import process

import uuid
import psutil
import Pyro4


from random import Random
from minerl.env import comms

logger = logging.getLogger(__name__)

malmo_version = "0.37.0"

class SeedType(IntEnum):
    """The seed type for an instance manager.
    
    Values:
        0 - NONE: No seeding whatsoever.
        1 - CONSTANT: All envrionments have the same seed (the one specified 
            to the instance manager) (or alist of seeds , separated)
        2 - GENERATED: All environments have different seeds generated from a single 
            random generator with the seed specified to the InstanceManager.
        3 - SPECIFIED: Each instance is given a list of seeds. Specify this like
            1,2,3,4;848,432,643;888,888,888
            Each instance's seed list is separated by ; and each seed is separated by ,
    """
    NONE = 0
    CONSTANT = 1
    GENERATED = 2
    SPECIFIED = 3



    @classmethod
    def get_index(cls, type):
        return list(cls).index(type)

        
MAXRAND = 1000000

INSTANCE_MANAGER_PYRO = 'minerl.instance_manager'
MINERL_INSTANCE_MANAGER_REMOTE = 'MINERL_INSTANCE_MANAGER_REMOTE'

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InstanceManager:
    """The Minecraft instance manager library. The instance manager can be used to allocate and safely terminate 
    existing Malmo instances for training agents. 
    
    Note: This object never needs to be explicitly invoked by the user of the MineRL library as the creation of
    one of the several MineRL environments will automatically query the InstanceManager to create a new instance.

    Note: In future versions of MineRL the instance manager will become its own daemon process which provides
    instance allocation capability using remote procedure calls.
    """
    MINECRAFT_DIR = os.path.join(os.path.dirname(__file__), 'Malmo', 'Minecraft') 
    SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), 'Malmo', 'Schemas') 
    STATUS_DIR = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'performance')
    MAXINSTANCES = None
    KEEP_ALIVE_PYRO_FREQUENCY = 5
    REMOTE = False

    DEFAULT_IP = "localhost"
    _instance_pool = []
    _malmo_base_port = 9000
    ninstances = 0
    X11_DIR = '/tmp/.X11-unix'
    headless = False
    managed = True
    _seed_type = SeedType.NONE
    _seed_generator = None

    @classmethod
    def _init_seeding(cls, seed_type=int(SeedType.NONE), seeds=None):
        """Sets the seeding type of the Instance manager object.
        
        Args:
            seed_type (SeedType, optional): The seed type of the instancemanger.. Defaults to SeedType.NONE.
            seed (long, optional): The initial seed of the instance manager. Defaults to None.
        
        Raises:
            TypeError: If the SeedType specified does not fall within the SeedType.
        """
        seed_type = int(seed_type)
        
        if seed_type == (SeedType.NONE):
            assert seeds is None, "Seed type set to NONE, therefore seed cannot be set."
        elif seed_type == (SeedType.CONSTANT):
            assert seeds is not None, "Seed set to constant seed, so seed must be specified."
            cls._seed_generator = [int(x) for x in seeds.split(",") if x]
        elif seed_type == (SeedType.GENERATED):
            assert seeds is not None, "Seed set to generated seed, so initial seed must be specified."
            cls._seed_generator = Random(int(seeds))
        elif seed_type == (SeedType.SPECIFIED):
            cls._seed_generator = ([[str(x) for x in s.split(",") if x] for s in seeds.split("-") if s])
        else:
            raise TypeError("Seed type {} not supported".format(seed_type))
        
        cls._seed_type  = seed_type

    @classmethod
    def _get_next_seed(cls, i=None):
        """Gets the next seed for an instance.
        
        Raises:
            TypeError: If the seed type cannot generate seeds.
        
        Returns:
            long: The seed generated by the seed type generator for seeds.  
        """
        if cls._seed_type == SeedType.CONSTANT:
            return cls._seed_generator
        elif cls._seed_type == SeedType.GENERATED:
            return [cls._seed_generator.randint(-MAXRAND, MAXRAND)]
        elif cls._seed_type == SeedType.SPECIFIED:
            try:
                if i is None: 
                    i = 0
                    logger.warning("Trying to use specified seed type without specifying index id.")
                return (cls._seed_generator[i])
            except IndexError:
                raise TypeError("Seed type {} ran out of seeds.".format(cls._seed_type))
        else:
            raise TypeError("Seed type {} does not support getting next seed".format(cls._seed_type))


    @classmethod
    def get_instance(cls, pid, instance_id=None):
        """
        Gets an instance from the instance manager. This method is a context manager
        and therefore when the context is entered the method yields a InstanceManager.Instance
        object which contains the allocated port and host for the given instance that was created.

        Yields:
            The allocated InstanceManager.Instance object.
        
        Raises:
            RuntimeError: No available instances or the maximum number of allocated instances reached.
            RuntimeError: No available instances and automatic allocation of instances is off.
        """
        if not instance_id:
            # Find an available instance.
            for inst in cls._instance_pool:
                if not inst.locked:
                    inst._acquire_lock(pid)
        

                    if hasattr(cls, "_pyroDaemon"):
                        cls._pyroDaemon.register(inst)
                        

                    return inst
        # Otherwise make a new instance if possible
        if cls.managed:
            if cls.MAXINSTANCES is None or cls.ninstances < cls.MAXINSTANCES:
                instance_id = cls.ninstances if instance_id is None else instance_id

                cls.ninstances += 1
                # Make the status directory.

                if hasattr(cls, "_pyroDaemon"):
                    status_dir = os.path.join(cls.STATUS_DIR, 'mc_{}'.format(cls.ninstances))
                    if not os.path.exists(status_dir):
                        os.makedirs(status_dir)
                else:
                    status_dir = None

                inst = cls.Instance(cls._get_valid_port(), status_dir=status_dir, instance_id=instance_id)
                cls._instance_pool.append(inst)
                inst._acquire_lock(pid)

                if hasattr(cls, "_pyroDaemon"):
                    cls._pyroDaemon.register(inst)

                return inst
 
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
            inst = cls.Instance(cls._get_valid_port())
            cls._instance_pool.append(inst)
        yield None
        cls.shutdown()

    @classmethod
    def add_existing_instance(cls, port,):
        assert cls._is_port_taken(port), "No Malmo mod utilizing the port specified."
        instance = InstanceManager.Instance(port=port, existing=True, status_dir=None)
        cls._instance_pool.append(instance)
        cls.ninstances += 1
        return instance

    @classmethod
    def add_keep_alive(cls,_pid, _callback):
        logger.debug("Recieved keep-alive callback from client {}. Starting thread.".format(_pid))
        def check_client_connected(client_pid, keep_alive_proxy):
            logger.debug("Client keep-alive connection monitor started for {}.".format(client_pid))
            while True:
                time.sleep(InstanceManager.KEEP_ALIVE_PYRO_FREQUENCY)
                try:
                    keep_alive_proxy.call()
                except:
                    bad_insts = [inst for inst in cls._instance_pool if inst.owner == client_pid]
                    for inst in bad_insts:
                        inst.close()

        keep_alive_thread = threading.Thread(
            target=check_client_connected,
            args=(_pid, _callback)
        )
        keep_alive_thread.setDaemon(True)
        keep_alive_thread.start()

    @staticmethod
    def _is_port_taken(port, address='0.0.0.0'):
        if psutil.MACOS  or psutil.AIX:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.bind((address, port))
                taken = False
            except socket.error as e:
                if e.errno in [98, 10048, 48]:
                    taken = True
                else:
                    raise e

            s.close()
            return taken
        else:
            ports = [x.laddr.port for x  in psutil.net_connections()]
            return port in ports

    @staticmethod
    def _is_display_port_taken(port, x11_path):
        return False

    @classmethod
    def _port_in_instance_pool(cls, port):
        # Ideally, this should be covered by other cases, but there may be delay
        # in when the ports get "used"
        return port in [instance.port for instance in cls._instance_pool]

    @classmethod
    def configure_malmo_base_port(cls, malmo_base_port):
        """Configure the lowest or base port for Malmo"""
        cls._malmo_base_port = malmo_base_port

    @classmethod
    def _get_valid_port(cls):
        malmo_base_port = cls._malmo_base_port
        port = (17 * os.getpid()) % 3989 + malmo_base_port
        port = (cls.ninstances  % 5000) + port
        while cls._is_port_taken(port) or \
              cls._is_display_port_taken(port - malmo_base_port, cls.X11_DIR) or \
              cls._port_in_instance_pool(port):
            port += 1
        return port


    @staticmethod
    def _process_watcher(parent_pid, child_pid, child_host, child_port, minecraft_dir, conn):
        """
        On *nix systems (perhaps Windows) this is the central code for killing the child if the parent dies.
        """
        port = child_port
        def port_watcher():
            nonlocal port 
            
            port = conn.recv()[0]

        port_thread = threading.Thread(target=port_watcher)
        port_thread.start()

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
                        try:
                            Instance._kill_minecraft_via_malmoenv(child_host,port)
                            time.sleep(2)
                        except:
                            pass
    
                        InstanceManager._reap_process_and_children(child)
                        try:
                            shutil.rmtree(minecraft_dir)
                        except:
                            logger.warning("Failed to delete temporary minecraft directory. It may have already been removed.")
                            pass
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

        procs = process.children(recursive=True) + [process]
        
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


    @classmethod
    def is_remote(cls):
        return cls.REMOTE



    @Pyro4.expose
    class Instance(object):
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
        MAX_PIPE_LENGTH = 500

        def __init__(self, port=None, existing=False, status_dir=None, seed=None, instance_id=None): 
            """
            Launches the subprocess.
            """
            self.running = False
            self._starting = True
            self.minecraft_process = None
            self.watcher_process = None
            self._port = port
            self._host = InstanceManager.DEFAULT_IP
            self.locked = False
            self.uuid = str(uuid.uuid4()).replace("-","")[:6]
            self.existing = existing
            self.minecraft_dir = None
            self.instance_dir = None
            self._status_dir = status_dir
            self.owner = None


            self.instance_id = instance_id

            # Try to set the seed for the instance using the instance manager's override.
            try:
                seed = InstanceManager._get_next_seed(instance_id)
            except TypeError as e:
                pass
            finally:
                # Even if the Instance manager does not override
                self._seed = seed

            self._setup_logging()
            self._target_port = port
            
        def launch(self, daemonize=False):
            port = self._target_port
            self._starting = True

            if not self.existing:
                if not port:
                    port = InstanceManager._get_valid_port()

                self.instance_dir = tempfile.mkdtemp()
                self.minecraft_dir = os.path.join(self.instance_dir, 'Minecraft')
                shutil.copytree(os.path.join(InstanceManager.MINECRAFT_DIR), self.minecraft_dir,
                                ignore=shutil.ignore_patterns('cache.properties.lock'))
                shutil.copytree(os.path.join(InstanceManager.SCHEMAS_DIR), os.path.join(self.instance_dir, 'Schemas'))

                    
                # 0. Get PID of launcher.
                parent_pid = os.getpid()
                # 1. Launch minecraft process and 
                self.minecraft_process=  self._launch_minecraft(
                    port, 
                    InstanceManager.headless,
                    self.minecraft_dir)

               
                # 2. Create a watcher process to ensure things get cleaned up
                if not daemonize:
                    self.watcher_process, update_port = self._launch_process_watcher(
                        parent_pid, self.minecraft_process.pid, self.host, port, self.instance_dir)
                else:
                    update_port = lambda x: None

                
                # wait until Minecraft process has outputed "CLIENT enter state: DORMANT"
                lines = []
                client_ready = False
                server_ready = False


                while True:
                    mine_log_encoding = locale.getpreferredencoding(False)
                    line = self.minecraft_process.stdout.readline().decode(mine_log_encoding)

                    # Check for failures and print useful messages!
                    _check_for_launch_errors(line)

                    if not line:
                        # IF THERE WAS AN ERROR STARTING THE MC PROCESS
                        # Print hte whole logs!
                        error_str = ""
                        for l in lines:
                            spline = "\n".join(l.split("\n")[:-1])
                            self._logger.error(spline)
                            error_str += spline +"\n"
                        # Throw an exception!
                        raise EOFError(error_str + "\n\nMinecraft process finished unexpectedly. There was an error with Malmo.")
                    
                    lines.append(line)
                    self._logger.debug("\n".join(line.split("\n")[:-1]))
                    

                    MALMOENVPORTSTR =  "***** Start MalmoEnvServer on port " 
                    port_received = MALMOENVPORTSTR in line
                    if port_received:
                        self._port = int(line.split(MALMOENVPORTSTR)[-1].strip())
                        # Send an update to the watcher process.
                        update_port(self._port)
                        
                    client_ready =  "CLIENT enter state: DORMANT" in line
                    server_ready =  "SERVER enter state: DORMANT" in line

                    if  client_ready:
                        break
                
                if not self.port:
                    raise RuntimeError("Malmo failed to start the MalmoEnv server! Check the logs from the Minecraft process.");
                self._logger.info("Minecraft process ready")
                 

                if not port == self._port:
                    self._logger.warning("Tried to launch Minecraft on port {} but that port was taken, instead Minecraft is using port {}.".format(port, self.port))
                # supress entire output, otherwise the subprocess will block
                # NB! there will be still logs under Malmo/Minecraft/run/logs
                # FNULL = open(os.devnull, 'w')
                # launch a logger process
                def log_to_file(logdir):
                    if not os.path.exists(os.path.join(logdir, 'logs')):
                            os.makedirs((os.path.join(logdir, 'logs')))

                    file_path = os.path.join(logdir, 'logs', 'mc_{}.log'.format(self._target_port - 9000))

                    logger.info("Logging output of Minecraft to {}".format(file_path))

                    mine_log = open(file_path, 'wb+')
                    mine_log.truncate(0)
                    mine_log_encoding = locale.getpreferredencoding(False)

                    try:
                        while self.running:
                            line = self.minecraft_process.stdout.readline()
                            if not line:
                                break
                            
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
                                    self._logger.error(linestr)
                            elif 'LOGTOPY' in linestr:
                                self._logger.info(linestr)
                            else:
                                self._logger.debug(linestr)
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

            self._starting = False

            # Make a hook to kill
            if not daemonize:
                atexit.register(lambda: self._destruct())

        def kill(self):
            """
            Kills the process (if it has been launched.)
            """
            self._destruct()
            pass

        def close(self):
            """Closes the object.
            """
            self._destruct(should_close=True)

        @property
        def status_dir(self):
            return self._status_dir

        @property
        def host(self):
            return self._host

        @property
        def port(self):
            return self._port

        def get_output(self):
            while self.running or self._starting:
                try:
                    level, line = self._output_stream.pop()
                    # print("didnt' get it")
                    return (line.levelno, line.getMessage(), line.name), self.running or self._starting
                except IndexError:
                    time.sleep(0.1)
            else:
                return None, False

        def _setup_logging(self):
            # Set up an output stream handler.
            self._logger = logging.getLogger(__name__ + ".instance.{}".format(str(self.uuid)))
            self._output_stream = collections.deque(maxlen=self.MAX_PIPE_LENGTH)
            for level in [logging.DEBUG]:
                handler = comms.QueueLogger(self._output_stream)
                handler.setLevel(level)
                self._logger.addHandler(handler)

        ###########################
        ##### PRIVATE METHODS #####
        ###########################
        def _launch_minecraft(self, port, headless, minecraft_dir):
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

            launch_script = os.path.join(minecraft_dir, launch_script)
            rundir = os.path.join(minecraft_dir, 'run')
            
            cmd = [launch_script, '-port', str(port), '-env', '-runDir', rundir]
            if self.status_dir:
                cmd += ['-performanceDir', self.status_dir]
            if self._seed:
                cmd += ['-seed', ",".join([str(x) for x in self._seed])]

            cmd_to_print = cmd[:] if not self._seed else cmd[:-2]
            self._logger.info("Starting Minecraft process: " + str(cmd_to_print))
            # print(cmd)

            if replaceable:
                cmd.append('-replaceable')
            preexec_fn = os.setsid if 'linux' in str(sys.platform) or sys.platform == 'darwin' else None
            # print(preexec_fn)
            minecraft_process = subprocess.Popen(cmd,
                cwd=InstanceManager.MINECRAFT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                # use process group, see http://stackoverflow.com/a/4791612/18576
                preexec_fn=preexec_fn
            )
            return minecraft_process

        def _launch_process_watcher(self, parent_pid, child_pid, child_host, child_port, minecraft_dir):
            """
            Launches the process watcher for the parent and minecraft process.
            """

            multiprocessing.freeze_support()
            parent_conn, child_conn = multiprocessing.Pipe()
            self._logger.info("Starting process watcher for process {} @ {}:{}".format(child_pid, child_host, child_port))
            p = multiprocessing.Process(
                target=InstanceManager._process_watcher, args=(
                    parent_pid, child_pid, 
                    child_host, child_port, 
                    minecraft_dir, child_conn))
                    
            def update_port(port):
                parent_conn.send([port])
            # p.daemon = True

            p.start()
            return p, update_port

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
                logger.error("Attempted to send kill command to minecraft process and failed.")
                return False

        def __del__(self):
            """
            On destruction of this instance kill the child.
            """
            self._destruct()

        def _destruct(self, should_close=False):
            """
            Do our best as the parent process to destruct and kill the child + watcher.
            """
            if (self.running or should_close) and not self.existing:
                self.running = False
                self._starting = False


                # Wait for the process to start.
                time.sleep(1)
                # kill the minecraft process and its subprocesses
                try:
                    shutil.rmtree(self.instance_dir)
                except:
                    print("Failed to delete the temporary minecraft directory.")

                if self._kill_minecraft_via_malmoenv(self.host, self.port):
                    # Let the minecraft process term on its own terms.
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
            pass

        
        def __repr__(self):
            return ("Malmo[{}, proc={}, addr={}:{}, locked={}]".format(
                self.uuid,
                self.minecraft_process.pid if not self.existing else "EXISTING",
                self.host,
                self.port,
                self.locked
            ))

        def _acquire_lock(self, owner=None):
            self.locked = True
            self.owner = owner

        def release_lock(self):
            self.locked = False
            self.owner = None


def _check_for_launch_errors(line):
    if "at org.lwjgl.opengl.Display.<clinit>" in line:
        raise  RuntimeError(
            "ERROR! MineRL could not detect an X Server, Monitor, or Virtual Monitor! "
            "\n"
            "\n"
            "In order to run minerl environments WITHOUT A HEAD use a software renderer such as 'xvfb':"
            "\n\t\txvfb-run python3 <your_script.py>"
            "\n\t! NOTE: xvfb conflicts with NVIDIA-drivers! "
            "\n\t! To run headless MineRL on a system with NVIDIA-drivers, please start a "
            "\n\t! vnc server of your choosing and then `export DISPLAY=:<insert ur vnc server #>"
            "\n\n"
            "If you're receiving this error and there is a monitor attached, make sure your current display"
            "variable is set correctly: "
            "\n\t\t DISPLAY=:0 python3 <your_script.py>"
            "\n\t! NOTE: For this to work your account must be logged on the physical monitor.\n\n"
            "If none of these steps work, please complain in the discord!\n"
            "If all else fails, JUST PUT THIS IN A DOCKER CONTAINER! :)"
        )
    if "Could not choose GLX13 config" in line:
        raise RuntimeError(
            "ERROR! MineRL could not detect any OpenGL libraries on your machine! \n"
            "To fix this please install an OpenGL supporting graphics driver."
            "\n\nIF THIS IS A HEADLESS LINUX MACHINE we reccomend Mesa:\n\n"
            "\tOn Ubuntu: \n"
            "\t\tsudo apt-get install libglu1-mesa-dev freeglut3-dev mesa-common-dev\n\n"
            "\tOn other distributions:\n"
            "\t\thttps://www.mesa3d.org/install.html\n\n"
            "\t (If this still isn't working you may have a conflicting NVIDIA driver.)\n"
            "\t (In which case you'll need to run minerl in a docker container)\n"
            "\n\n"
            "IF YOU THIS IS NOT A HEADLESS MACHINE please install graphics drivers on your system!"
            "\n"
            "\n"
            "If none of these steps work, please complain in discord!\n"
            "If all else fails, JUST PUT THIS IN A DOCKER CONTAINER! :)")



def launch_queue_logger_thread(output_producer, should_end):
    def queue_logger_thread(out_prod, should_end):
        while not should_end():
            try:
                line, running = out_prod.get_output()
                if not running:
                    break
                if line:
                    level = line[0]
                    record = line[1]
                    name = line[2]
                    lgr = logging.getLogger(name)
                    lgr.log(level, record)
            except Exception as e:
                print(e)
                break
        
    
    thread = threading.Thread(
        target=queue_logger_thread,
        args=(output_producer, should_end))
    thread.setDaemon(True)
    thread.start()
            


def launch_instance_manager():
    """Defines the entry point for the remote procedure call server.
    """
    # Todo: Use name servers in the docker contexct (set up a docker compose?)
    # pyro4-ns
    parser = argparse.ArgumentParser("python3 launch_instance_manager.py")
    parser.add_argument("--seeds", type=str, default=None, 
        help="The default seed for the environment.")
    parser.add_argument("--seeding_type", type=str, default=SeedType.CONSTANT, 
        help="The seeding type for the environment. Defaults to 1 (CONSTANT)"
             "if a seed specified, otherwise 0 (NONE): \n{}".format(SeedType.__doc__))

    
    parser.add_argument("--max_instances", type=int, default=None,
        help="The maximum number of instances the instance manager is able to spawn,"
              "before an exception is thrown. Defaults to Unlimited.")
    opts = parser.parse_args()

    
    if opts.max_instances is not None:
        assert opts.max_instances > 0, "Maximum instances must be more than zero!"
        InstanceManager.MAXINSTANCES = opts.max_instances
    

    try:
        print("Removing the performance directory!")
        try:
            shutil.rmtree(InstanceManager.STATUS_DIR)
        except:
            pass
        finally:
            if not os.path.exists(InstanceManager.STATUS_DIR):
                os.makedirs(InstanceManager.STATUS_DIR)
        print("autoproxy?",Pyro4.config.AUTOPROXY)
        InstanceManager.REMOTE = True
        Pyro4.config.COMMTIMEOUT = InstanceManager.KEEP_ALIVE_PYRO_FREQUENCY  

        # Initialize seeding.
        if opts.seeds is not None:
            InstanceManager._init_seeding(seeds=opts.seeds, seed_type=opts.seeding_type)
        else:
            InstanceManager._init_seeding(seed_type=SeedType.NONE)

        
        Pyro4.Daemon.serveSimple(
            {
                InstanceManager: INSTANCE_MANAGER_PYRO
            },
            ns = True)
        
    except Pyro4.errors.NamingError as e:
        print(e)
        print("Start the Pyro name server with pyro4-ns and re-run this script.")


class CustomAsyncRemoteMethod(Pyro4.core._AsyncRemoteMethod):
    def __call__(self, *args, **kwargs):
        res = super().__call__(*args, **kwargs)
        val = res.value
        if isinstance(val, Pyro4.Proxy):
            val._pyroAsync(asynchronous=True)
 
        return val


if os.getenv(MINERL_INSTANCE_MANAGER_REMOTE):
    sys.excepthook = Pyro4.util.excepthook  
    Pyro4.core._AsyncRemoteMethod = CustomAsyncRemoteMethod     
    InstanceManager = Pyro4.Proxy("PYRONAME:" + INSTANCE_MANAGER_PYRO )
    InstanceManager._pyroAsync(asynchronous=True)

    # Set up the keep alive signal.
    logger.debug("Starting client keep-alive server...")
    def keep_alive_pyro():
        class KeepAlive(object):
            @Pyro4.expose
            @Pyro4.callback
            def call(self):
                return True

        daemon = Pyro4.core.Daemon()
        callback = KeepAlive()
        daemon.register(callback)

        InstanceManager.add_keep_alive(os.getpid(), callback)

        logger.debug("Client keep-alive server started.")
        daemon.requestLoop()

    thread = threading.Thread(target=keep_alive_pyro)
    thread.setDaemon(True)
    thread.start()
        
        
