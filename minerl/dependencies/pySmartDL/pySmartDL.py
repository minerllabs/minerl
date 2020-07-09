import os
import sys
import urllib.request, urllib.error, urllib.parse
import copy
import threading
import time
import math
import tempfile
import base64
import hashlib
import socket
import logging
from io import StringIO
import multiprocessing.dummy as multiprocessing
from ctypes import c_int
import json

from . import utils
from .control_thread import ControlThread
from .download import download

__all__ = ['SmartDL', 'utils']
__version_mjaor__ = 1
__version_minor__ = 3
__version_micro__ = 4
__version__ = "{}.{}.{}".format(__version_mjaor__, __version_minor__, __version_micro__)

class HashFailedException(Exception):
    "Raised when hash check fails."
    def __init__(self, fn, calc_hash, needed_hash):
        self.filename = fn
        self.calculated_hash = calc_hash
        self.needed_hash = needed_hash
    def __str__(self):
        return 'HashFailedException({}, got {}, expected {})'.format(self.filename, self.calculated_hash, self.needed_hash)
    def __repr__(self):
        return '<HashFailedException {}, got {}, expected {}>'.format(self.filename, self.calculated_hash, self.needed_hash)
        
class CanceledException(Exception):
    "Raised when the job is canceled."
    def __init__(self):
        pass
    def __str__(self):
        return 'CanceledException'
    def __repr__(self):
        return "<CanceledException>"

class SmartDL:
    '''
    The main SmartDL class
    
    :param urls: Download url. It is possible to pass unsafe and unicode characters. You can also pass a list of urls, and those will be used as mirrors.
    :type urls: string or list of strings
    :param dest: Destination path. Default is `%TEMP%/pySmartDL/`.
    :type dest: string
    :param progress_bar: If True, prints a progress bar to the `stdout stream <http://docs.python.org/2/library/sys.html#sys.stdout>`_. Default is `True`.
    :type progress_bar: bool
	:param fix_urls: If true, attempts to fix urls with unsafe characters.
	:type fix_urls: bool
	:param threads: Number of threads to use.
	:type threads: int
    :param timeout: Timeout for network operations, in seconds. Default is 5.
	:type timeout: int
    :param logger: An optional logger.
    :type logger: `logging.Logger` instance
    :param connect_default_logger: If true, connects a default logger to the class.
    :type connect_default_logger: bool
    :param request_args: Arguments to be passed to a new urllib.request.Request instance in dictionary form. See `urllib.request docs <https://docs.python.org/3/library/urllib.request.html#urllib.request.Request>`_ for options. 
    :type request_args: dict
    :rtype: `SmartDL` instance
    
    .. NOTE::
            The provided dest may be a folder or a full path name (including filename). The workflow is:
            
            * If the path exists, and it's an existing folder, the file will be downloaded to there with the original filename.
            * If the past does not exist, it will create the folders, if needed, and refer to the last section of the path as the filename.
            * If you want to download to folder that does not exist at the moment, and want the module to fill in the filename, make sure the path ends with `os.sep`.
            * If no path is provided, `%TEMP%/pySmartDL/` will be used.
    '''
    
    def __init__(self, urls, dest=None, progress_bar=True, fix_urls=True, threads=5, timeout=5, logger=None, connect_default_logger=False, request_args=None):
        if logger:
            self.logger = logger
        elif connect_default_logger:
            self.logger = utils.create_debugging_logger()
        else:
            self.logger = utils.DummyLogger()
        if request_args:
            if "headers" not in request_args:
                request_args["headers"] = dict()
            self.requestArgs = request_args
        else:
            self.requestArgs = {"headers": dict()}
        if "User-Agent" not in self.requestArgs["headers"]:
            self.requestArgs["headers"]["User-Agent"] = utils.get_random_useragent()
        self.mirrors = [urls] if isinstance(urls, str) else urls
        if fix_urls:
            self.mirrors = [utils.url_fix(x) for x in self.mirrors]
        self.url = self.mirrors.pop(0)
        self.logger.info('Using url "{}"'.format(self.url))

        fn = urllib.parse.unquote(os.path.basename(urllib.parse.urlparse(self.url).path))
        self.dest = dest or os.path.join(tempfile.gettempdir(), 'pySmartDL', fn)
        if self.dest[-1] == os.sep:
            if os.path.exists(self.dest[:-1]) and os.path.isfile(self.dest[:-1]):
                os.unlink(self.dest[:-1])
            self.dest += fn
        if os.path.isdir(self.dest):
            self.dest = os.path.join(self.dest, fn)
        
        self.progress_bar = progress_bar
        self.threads_count = threads
        self.timeout = timeout
        self.current_attemp = 1 
        self.attemps_limit = 4
        self.minChunkFile = 1024**2*2 # 2MB
        self.filesize = 0
        self.shared_var = multiprocessing.Value(c_int, 0)  # a ctypes var that counts the bytes already downloaded
        self.thread_shared_cmds = {}
        self.status = "ready"
        self.verify_hash = False
        self._killed = False
        self._failed = False
        self._start_func_blocking = True
        self.errors = []
        
        self.post_threadpool_thread = None
        self.control_thread = None
        
        if not os.path.exists(os.path.dirname(self.dest)):
            self.logger.info('Folder "{}" does not exist. Creating...'.format(os.path.dirname(self.dest)))
            os.makedirs(os.path.dirname(self.dest))
        if not utils.is_HTTPRange_supported(self.url, timeout=self.timeout):
            self.logger.warning("Server does not support HTTPRange. threads_count is set to 1.")
            self.threads_count = 1
        if os.path.exists(self.dest):
            self.logger.warning('Destination "{}" already exists. Existing file will be removed.'.format(self.dest))
        if not os.path.exists(os.path.dirname(self.dest)):
            self.logger.warning('Directory "{}" does not exist. Creating it...'.format(os.path.dirname(self.dest)))
            os.makedirs(os.path.dirname(self.dest))
        
        self.logger.info("Creating a ThreadPool of {} thread(s).".format(self.threads_count))
        self.pool = utils.ManagedThreadPoolExecutor(self.threads_count)
        
    def __str__(self):
        return 'SmartDL(r"{}", dest=r"{}")'.format(self.url, self.dest)

    def __repr__(self):
        return "<SmartDL {}>".format(self.url)
        
    def add_basic_authentication(self, username, password):
        '''
        Uses HTTP Basic Access authentication for the connection.
        
        :param username: Username.
        :type username: string
        :param password: Password.
        :type password: string
        '''
        auth_string = '{}:{}'.format(username, password)
        base64string = base64.standard_b64encode(auth_string.encode('utf-8'))
        self.requestArgs['headers']['Authorization'] = b"Basic " + base64string
        
    def add_hash_verification(self, algorithm, hash):
        '''
        Adds hash verification to the download.
        
        If hash is not correct, will try different mirrors. If all mirrors aren't
        passing hash verification, `HashFailedException` Exception will be raised.
        
        .. NOTE::
            If downloaded file already exist on the destination, and hash matches, pySmartDL will not download it again.
            
        .. WARNING::
            The hashing algorithm must be supported on your system, as documented at `hashlib documentation page <http://docs.python.org/3/library/hashlib.html>`_.
        
        :param algorithm: Hashing algorithm.
        :type algorithm: string
        :param hash: Hash code.
        :type hash: string
        '''
        
        self.verify_hash = True
        self.hash_algorithm = algorithm
        self.hash_code = hash
        
    def fetch_hash_sums(self):
        '''
        Will attempt to fetch UNIX hash sums files (`SHA256SUMS`, `SHA1SUMS` or `MD5SUMS` files in
        the same url directory).
        
        Calls `self.add_hash_verification` if successful. Returns if a matching hash was found.
        
        :rtype: bool
        
        *New in 1.2.1*
        '''
        default_sums_filenames = ['SHA256SUMS', 'SHA1SUMS', 'MD5SUMS']
        folder = os.path.dirname(self.url)
        orig_basename = os.path.basename(self.url)
        
        self.logger.info("Looking for SUMS files...")
        for filename in default_sums_filenames:
            try:
                sums_url = "%s/%s" % (folder, filename)
                sumsRequest = urllib.request.Request(sums_url, **self.requestArgs)
                obj = urllib.request.urlopen(sumsRequest)
                data = obj.read().split('\n')
                obj.close()
                
                for line in data:
                    if orig_basename.lower() in line.lower():
                        self.logger.info("Found a matching hash in %s" % sums_url)
                        algo = filename.rstrip('SUMS')
                        hash = line.split(' ')[0]
                        self.add_hash_verification(algo, hash)
                        return
                
            except urllib.error.HTTPError:
                continue
        
    def start(self, blocking=None):
        '''
        Starts the download task. Will raise `RuntimeError` if it's the object's already downloading.
        
        .. warning::
            If you're using the non-blocking mode, Exceptions won't be raised. In that case, call
            `isSuccessful()` after the task is finished, to make sure the download succeeded. Call
            `get_errors()` to get the the exceptions.
        
        :param blocking: If true, calling this function will block the thread until the download finished. Default is *True*.
        :type blocking: bool
        '''
        if not self.status == "ready":
            raise RuntimeError("cannot start (current status is {})".format(self.status))
        self.logger.info('Starting a new SmartDL operation.')

        if blocking is None:
            blocking = self._start_func_blocking
        else:
            self._start_func_blocking = blocking
        
        if self.mirrors:
            self.logger.info('One URL and {} mirrors are loaded.'.format(len(self.mirrors)))
        else:
            self.logger.info('One URL is loaded.')
        
        if self.verify_hash and os.path.exists(self.dest):
            if utils.get_file_hash(self.hash_algorithm, self.dest) == self.hash_code:
                self.logger.info("Destination '%s' already exists, and the hash matches. No need to download." % self.dest)
                self.status = 'finished'
                return
        
        self.logger.info("Downloading '{}' to '{}'...".format(self.url, self.dest))
        req = urllib.request.Request(self.url, **self.requestArgs)
        try:
            urlObj = urllib.request.urlopen(req, timeout=self.timeout)
        except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout) as e:
            self.errors.append(e)
            if self.mirrors:
                self.logger.info("{} Trying next mirror...".format(str(e)))
                self.url = self.mirrors.pop(0)
                self.logger.info('Using url "{}"'.format(self.url))
                self.start(blocking)
                return
            else:
                self.logger.warning(str(e))
                self.errors.append(e)
                self._failed = True
                self.status = "finished"
                raise
        
        try:
            self.filesize = int(urlObj.headers["Content-Length"])
            self.logger.info("Content-Length is {} ({}).".format(self.filesize, utils.sizeof_human(self.filesize)))
        except (IndexError, KeyError, TypeError):
            self.logger.warning("Server did not send Content-Length. Filesize is unknown.")
            self.filesize = 0
            
        args = utils.calc_chunk_size(self.filesize, self.threads_count, self.minChunkFile)
        bytes_per_thread = args[0][1] - args[0][0] + 1
        if len(args)>1:
            self.logger.info("Launching {} threads (downloads {}/thread).".format(len(args),  utils.sizeof_human(bytes_per_thread)))
        else:
            self.logger.info("Launching 1 thread (downloads {}).".format(utils.sizeof_human(bytes_per_thread)))
        
        self.status = "downloading"
        
        for i, arg in enumerate(args):
            req = self.pool.submit(
                download,
                self.url,
                self.dest+".%.3d" % i,
                self.requestArgs,
                arg[0],
                arg[1],
                self.timeout,
                self.shared_var,
                self.thread_shared_cmds,
                self.logger
            )
        
        self.post_threadpool_thread = threading.Thread(
            target=post_threadpool_actions,
            args=(
                self.pool,
                [[(self.dest+".%.3d" % i) for i in range(len(args))], self.dest],
                self.filesize,
                self
            )
        )
        self.post_threadpool_thread.daemon = True
        self.post_threadpool_thread.start()
        
        self.control_thread = ControlThread(self)
        
        if blocking:
            self.wait(raise_exceptions=True)
            
    def _exc_callback(self, req, e):
        self.errors.append(e[0])
        self.logger.exception(e[1])
        
    def retry(self, eStr=""):
        if self.current_attemp < self.attemps_limit:
            self.current_attemp += 1
            self.status = "ready"
            self.shared_var.value = 0
            self.thread_shared_cmds = {}
            self.start()
             
        else:
            s = 'The maximum retry attempts reached'
            if eStr:
                s += " ({})".format(eStr)
            self.errors.append(urllib.error.HTTPError(self.url, "0", s, {}, StringIO()))
            self._failed = True
            
    def try_next_mirror(self, e=None):
        if self.mirrors:
            if e:
                self.errors.append(e)
            self.status = "ready"
            self.shared_var.value = 0
            self.url = self.mirrors.pop(0)
            self.logger.info('Using url "{}"'.format(self.url))
            self.start()
        else:
            self._failed = True
            self.errors.append(e)
    
    def get_eta(self, human=False):
        '''
        Get estimated time of download completion, in seconds. Returns `0` if there is
        no enough data to calculate the estimated time (this will happen on the approx.
        first 5 seconds of each download).
        
        :param human: If true, returns a human-readable formatted string. Else, returns an int type number
        :type human: bool
        :rtype: int/string
        '''
        if human:
            s = utils.time_human(self.control_thread.get_eta())
            return s if s else "TBD"
        return self.control_thread.get_eta()

    def get_speed(self, human=False):
        '''
        Get current transfer speed in bytes per second.
        
        :param human: If true, returns a human-readable formatted string. Else, returns an int type number
        :type human: bool
        :rtype: int/string
        '''
        if human:
            return "{}/s".format(utils.sizeof_human(self.control_thread.get_speed()))
        return self.control_thread.get_speed()

    def get_progress(self):
        '''
        Returns the current progress of the download, as a float between `0` and `1`.
        
        :rtype: float
        '''
        if not self.filesize:
            return 0
        if self.control_thread.get_dl_size() <= self.filesize:
            return 1.0*self.control_thread.get_dl_size()/self.filesize
        return 1.0

    def get_progress_bar(self, length=20):
        '''
        Returns the current progress of the download as a string containing a progress bar.
        
        .. NOTE::
            That's an alias for pySmartDL.utils.progress_bar(obj.get_progress()).
        
        :param length: The length of the progress bar in chars. Default is 20.
        :type length: int
        :rtype: string
        '''
        return utils.progress_bar(self.get_progress(), length)

    def isFinished(self):
        '''
        Returns if the task is finished.
        
        :rtype: bool
        '''
        if self.status == "ready":
            return False
        if self.status == "finished":
            return True
        return not self.post_threadpool_thread.is_alive()

    def isSuccessful(self):
        '''
        Returns if the download is successfull. It may fail in the following scenarios:
        
        - Hash check is enabled and fails.
        - All mirrors are down.
        - Any local I/O problems (such as `no disk space available`).
        
        .. NOTE::
            Call `get_errors()` to get the exceptions, if any.
        
        Will raise `RuntimeError` if it's called when the download task is not finished yet.
        
        :rtype: bool
        '''
        
        if self._killed:
            return False
        
        n = 0
        while self.status != 'finished':
            n += 1
            time.sleep(0.1)
            if n >= 15:
                raise RuntimeError("The download task must be finished in order to see if it's successful. (current status is {})".format(self.status))
            
        return not self._failed
        
    def get_errors(self):
        '''
        Get errors happened while downloading.
        
        :rtype: list of `Exception` instances
        '''
        return self.errors
        
    def get_status(self):
        '''
        Returns the current status of the task. Possible values: *ready*,
        *downloading*, *paused*, *combining*, *finished*.
        
        :rtype: string
        '''
        return self.status

    def wait(self, raise_exceptions=False):
        '''
        Blocks until the download is finished.
        
        :param raise_exceptions: If true, this function will raise exceptions. Default is *False*.
        :type raise_exceptions: bool
        '''
        if self.status in ["ready", "finished"]:
            return
            
        while not self.isFinished():
            time.sleep(0.1)
        self.post_threadpool_thread.join()
        self.control_thread.join()
        
        if self._failed and raise_exceptions:
            raise self.errors[-1]

    def stop(self):
        '''
        Stops the download.
        '''
        if self.status == "downloading":
            self.thread_shared_cmds['stop'] = ""
            self._killed = True

    def pause(self):
        '''
        Pauses the download.
        '''
        if self.status == "downloading":
            self.status = "paused"
            self.thread_shared_cmds['pause'] = ""

    def resume(self):
        '''
        Continues the download. same as unpause().
        '''
        self.unpause()

    def unpause(self):
        '''
        Continues the download. same as resume().
        '''
        if self.status == "paused" and 'pause' in self.thread_shared_cmds:
            self.status = "downloading"
            del self.thread_shared_cmds['pause']
    
    def limit_speed(self, speed):
        '''
        Limits the download transfer speed.
        
        :param speed: Speed in bytes per download per second. Negative values will not limit the speed. Default is `-1`.
        :type speed: int
        '''
        if self.status == "downloading":
            if speed == 0:
                self.pause()
            else:
                self.unpause()

        if speed > 0:
            self.thread_shared_cmds['limit'] = speed/self.threads_count
        elif 'limit' in self.thread_shared_cmds:
            del self.thread_shared_cmds['limit']
        
    def get_dest(self):
        '''
        Get the destination path of the downloaded file. Needed when no
        destination is provided to the class, and exists on a temp folder.
        
        :rtype: string
        '''
        return self.dest
    def get_dl_time(self, human=False):
        '''
        Returns how much time did the download take, in seconds. Returns
        `-1` if the download task is not finished yet.

        :param human: If true, returns a human-readable formatted string. Else, returns an int type number
        :type human: bool
        :rtype: int/string
        '''
        if not self.control_thread:
            return 0
        if human:
            return utils.time_human(self.control_thread.get_dl_time())
        return self.control_thread.get_dl_time()
        
    def get_dl_size(self, human=False):
        '''
        Get downloaded bytes counter in bytes.
        
        :param human: If true, returns a human-readable formatted string. Else, returns an int type number
        :type human: bool
        :rtype: int/string
        '''
        if not self.control_thread:
            return 0
        if human:
            return utils.sizeof_human(self.control_thread.get_dl_size())    
        return self.control_thread.get_dl_size()

    def get_final_filesize(self, human=False):
        '''
        Get total download size in bytes.
        
        :param human: If true, returns a human-readable formatted string. Else, returns an int type number
        :type human: bool
        :rtype: int/string
        '''
        if not self.control_thread:
            return 0
        if human:
            return utils.sizeof_human(self.control_thread.get_final_filesize())    
        return self.control_thread.get_final_filesize()
    
    
    def get_data(self, binary=False, bytes=-1):
        '''
        Returns the downloaded data. Will raise `RuntimeError` if it's
        called when the download task is not finished yet.
        
        :param binary: If true, will read the data as binary. Else, will read it as text.
        :type binary: bool
        :param bytes: Number of bytes to read. Negative values will read until EOF. Default is `-1`.
        :type bytes: int
        :rtype: string
        '''
        if self.status != 'finished':
            raise RuntimeError("The download task must be finished in order to read the data. (current status is %s)" % self.status)
            
        flags = 'rb' if binary else 'r'
        with open(self.get_dest(), flags) as f:
            data = f.read(bytes) if bytes>0 else f.read()
        return data
        
    def get_data_hash(self, algorithm):
        '''
        Returns the downloaded data's hash. Will raise `RuntimeError` if it's
        called when the download task is not finished yet.
        
        :param algorithm: Hashing algorithm.
        :type algorithm: bool
        :rtype: string
        
        .. WARNING::
            The hashing algorithm must be supported on your system, as documented at `hashlib documentation page <http://docs.python.org/3/library/hashlib.html>`_.
        '''
        return hashlib.new(algorithm, self.get_data(binary=True)).hexdigest()

    def get_json(self):
        '''
        Returns the JSON in the downloaded data. Will raise `RuntimeError` if it's
        called when the download task is not finished yet. Will raise `json.decoder.JSONDecodeError`
        if the downloaded data is not valid JSON.
        
        :rtype: dict
        '''
        data = self.get_data()
        return json.loads(data)

def post_threadpool_actions(pool, args, expected_filesize, SmartDLObj):
    "Run function after thread pool is done. Run this in a thread."
    while not pool.done():
        time.sleep(0.1)

    if SmartDLObj._killed:
        return
        
    if pool.get_exception():
        for exc in pool.get_exceptions():
            SmartDLObj.logger.exception(exc)
            
        SmartDLObj.retry(str(pool.get_exception()))
       
    if SmartDLObj._failed:
        SmartDLObj.logger.warning("Task had errors. Exiting...")
        return
        
    if expected_filesize:  # if not zero, expected filesize is known
        threads = len(args[0])
        total_filesize = sum([os.path.getsize(x) for x in args[0]])
        diff = math.fabs(expected_filesize - total_filesize)
        
        # if the difference is more than 4*thread numbers (because a thread may download 4KB extra per thread because of NTFS's block size)
        if diff > 4*1024*threads:
            errMsg = 'Diff between downloaded files and expected filesizes is {}B (filesize: {}, expected_filesize: {}, {} threads).'.format(total_filesize, expected_filesize, diff, threads)
            SmartDLObj.logger.warning(errMsg)
            SmartDLObj.retry(errMsg)
            return
    
    SmartDLObj.status = "combining"
    utils.combine_files(*args)
    
    if SmartDLObj.verify_hash:
        dest_path = args[-1]            
        hash_ = utils.get_file_hash(SmartDLObj.hash_algorithm, dest_path)
	
        if hash_ == SmartDLObj.hash_code:
            SmartDLObj.logger.info('Hash verification succeeded.')
        else:
            SmartDLObj.logger.warning('Hash verification failed.')
            SmartDLObj.try_next_mirror(HashFailedException(os.path.basename(dest_path), hash, SmartDLObj.hash_code))
