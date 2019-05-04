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
import atexit
import multiprocessing
import time
# from exceptions import NotImplementedError
from multiprocessing import process
from pydoc import replace

from minerl.env.version import malmo_branch, malmo_version

malmo_dir = os.path.join(os.path.dirname(__file__), 'Malmo')
PORT_SEARCH_RANGE = 20000 # Max number of ports to probe
PORT_MAX = 65000 # The max port numb we can check to.


def download(branch=malmo_branch, build=True, installdir=malmo_dir):
    """Download Malmo from github and build (by default) the Minecraft Mod.
    Args:
        branch: optional branch to clone. TODO Default is release version.
        build: build the Mod unless build arg is given as False.
        installdir: the install dir name. Defaults to MalmoPlatform.
    Returns:
        The path for the Malmo Minecraft mod.
    """
    # TODO: ADD VERSIONING BEFORE RELEASE !!!!!!!!!!!!!!!!!

    if branch is None:
        branch = malmo_version

    # Check to see if the minerlENV is set up yet.
    if os.path.exists(malmo_dir):
        # TODO CHECK TO SEE IF THE VERSION MATCHES THE PYTHON VERSION!
        # TODO CHECKT OSEE THAT DECOMP WORKSPACE HAS BEEN SET UP (write a finished txt)
        return
    
    # If it exists lets set up the env.
    # TODO: Convert to using loggers.
    print("❤️❤️❤️ Hello! Welcome to MineRL Env ❤️❤️❤️")
    print("MineRL is not yet setup for this package install! Downloading and installing Malmo backend.")

    try:
        subprocess.check_call(["git", "clone", "-b", branch, "https://github.com/cmu-rl/malmo.git", malmo_dir])
    except subprocess.CalledProcessError:
        print("ATTENTION: Setup failed! Was permission denied? "
              "If so you  installed the library using sudo (or a different user)."
              "Try rerunning the script as with sudo (or the user which you installed MineRL with).")

    return setup(build=build, installdir=installdir)


def setup(build=True, installdir=malmo_dir):
    """Set up Minecraft for use with the MalmoEnv gym environment"""

    gradlew = './gradlew'
    if os.name == 'nt':
        gradlew = 'gradlew.bat'

    cwd = os.getcwd()
    os.chdir(installdir)
    os.chdir("Minecraft")
    try:
        # Create the version properties file.
        pathlib.Path("src/main/resources/version.properties").write_text("malmomod.version={}\n".format(malmo_version))
        # Optionally do a test build.
        if build:
            subprocess.check_call([gradlew, "setupDecompWorkspace", "build", "testClasses",
                                   "-x", "test", "--stacktrace", "-Pversion={}".format(malmo_version)])
        minecraft_dir = os.getcwd()
    finally:
        os.chdir(cwd)
    return minecraft_dir


class MinecraftInstance(object):
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

    def __init__(self):
        """
        Launches the subprocess.
        """
        self.running = False
        self.minecraft_process = None
        self.watcher_process = None
        self._port = -1
        self._host = 'localhost'
        pass

    def launch(self, port : int, headless=False):
        if headless:
            raise NotImplementedError("Headless mode is not yet supported.")

        # 0. Get PID of launcher.
        parent_pid = os.getpid()
        # 1. Launch child process
        available_port = MinecraftInstance._find_ports(self.host, port)
        self.minecraft_process = self._launch_minecraft(port)
        # 2. Launch watcher process
        self.watcher_process = self._launch_process_watcher(
            parent_pid, self.minecraft_process.pid)

        self.running = True
        self._port = port

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
    def _launch_minecraft(self, port, installdir=malmo_dir):
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
        launch_script = './launchClient.sh'
        if os.name == 'nt':
            launch_script = 'launchClient.bat'
        cwd = os.getcwd()
        os.chdir(installdir)
        os.chdir("Minecraft")
        # First let's pull for updates ;)
        # try: 
            # subprocess.check_call(["git", "pull"])
        # finally:
            # pass
        
        try:
            cmd = [launch_script, '-port', str(port), '-env']
            if replaceable:
                cmd.append('-replaceable')
            minecraft_process = subprocess.Popen(cmd,
                # stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        finally:
            os.chdir(cwd)
        return minecraft_process

    def _launch_process_watcher(self, parent_pid, child_pid):
        """
        Launches the process watcher for the parent and miencraft process.
        """
        p = multiprocessing.Process(
            target=MinecraftInstance._process_watcher, args=(parent_pid, child_pid))
        # p.daemon = True
        p.start()
        return p

    @staticmethod
    def _find_ports(host, initial_port):
        """
        Finds an available port by probing and incrementing from the initial port provided.
        """
        found_port = False
        port = initial_port -1
        while not found_port:
            port +=1
            if  port >= max(initial_port + PORT_SEARCH_RANGE, PORT_MAX): 
                raise RuntimeError(
                    "No ports in the range {} - {} found for Minecraft. Try killing some environments or starting with a lower initial port!".format(
                    initial_port, port
                ))
            found_port = _check_port_avail(host, port)
        else:
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
                        _reap_process_and_children(child)
                    return
                # Kill the watcher if the child is no longer running.
                # If you want to attempt to restart the child on failure, this
                # would be the location to do so.
                if not child.is_running():
                    return
            except KeyboardInterrupt:
                pass

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
                _reap_process_and_children(psutil.Process(self.minecraft_process.pid))
            except psutil.NoSuchProcess: 
                pass
            # killall the watcher
            # try:
            self.watcher_process.terminate()

            self.running = False
        pass


def _reap_process_and_children(process, timeout=3):
    "Tries hard to terminate and ultimately kill all the children of this process."
    def on_terminate(proc):
        print("process {} terminated with exit code {}".format(proc, proc.returncode))

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
            print("process {} survived SIGTERM; trying SIGKILL".format(p.pid))
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass
        gone, alive = psutil.wait_procs(alive, timeout=timeout, callback=on_terminate)
        if alive:
            # give up
            for p in alive:
                print("process {} survived SIGKILL; giving up".format(p.pid))


def _check_port_avail(host : str, port_num : int):
    """
    Checks if a port is available or not.
    """
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host,port_num))
    sock.close()

    return result == 0
