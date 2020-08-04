import os.path
import sys
import urllib
import atexit
import requests
import shutil
import hashlib
import logging
import tqdm
import time
import numpy as np

from urllib.error import HTTPError

import queue
import concurrent.futures
import threading
from typing import Callable, Any
from collections import OrderedDict

from minerl.data.util.blacklist import Blacklist


def multimap(f: Callable, *xs: Any) -> Any:
    """
    Each x in xs is a tree of the same structure.
    Apply f at each leaf of the tree with len(xs) arguments.
    Return a tree of the same structure, where each leaf contains f's return value.
    """
    first = xs[0]
    if isinstance(first, dict) or isinstance(first, OrderedDict):
        assert all(isinstance(x, dict) or isinstance(x, OrderedDict) for x in xs)
        assert all(x.keys() == first.keys() for x in xs)
        return {k: multimap(f, *(x[k] for x in xs)) for k in sorted(first.keys())}
    else:
        return f(*xs)


def forever():
    i = 0
    while True:
        i += 1
        yield i


def validate_file(file_path, hash):
    """
    Validates a file against an MD5 hash value
 
    :param file_path: path to the file for hash validation
    :type file_path:  string
    :param hash:      expected hash value of the file
    :type hash:       string -- MD5 hash value
    """
    m = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(1000 * 1000)  # 1MB
            if not chunk:
                break
            m.update(chunk)
    return m.hexdigest() == hash


def get_mirror(urls) -> requests.Response:
    # Interactive python downloads dont get fancy as_completed support =(
    if bool(getattr(sys, 'ps1', sys.flags.interactive)):
        reqs = [requests.head(url) for url in urls]
        successes = [req for req in reqs if req.status_code == 200]
        if len(successes) > 0:
            return min(successes, key=lambda r: r.elapsed.seconds)
        else:
            req = min(reqs, key=lambda r: r.elapsed.seconds)
            raise HTTPError(req.url, req.status_code, "resource not found", req.headers, None)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as worker_pool:
            futures = [worker_pool.submit(requests.head, url) for url in urls]
            first_request = None
            for future in concurrent.futures.as_completed(futures):
                request = future.result()
                first_request = request if first_request is None else first_request
                if request.status_code == 200:
                    return request
                else:
                    logging.warning('Mirror {} returned status code {}'.format(request.url, request.status_code))
            raise HTTPError(first_request.url, first_request.status_code, "resource not found", first_request.headers, None)


def download_with_resume(urls, file_path, hash=None, timeout=10):
    """
    Performs a HTTP(S) download that can be restarted if prematurely terminated.
    The HTTP server must support byte ranges.
 
    :param file_path: the path to the file to write to disk
    :type file_path:  string
    :param hash: hash value for file validation
    :type hash:  string (MD5 hash value)
    """
    # don't download if the file exists
    if os.path.exists(file_path):
        logging.info("File already exists.")
        return
    block_size = 1000 * 1000  # 1MB
    tmp_file_path = file_path + '.part'
    first_byte = os.path.getsize(tmp_file_path) if os.path.exists(tmp_file_path) else 0
    file_mode = 'ab' if first_byte else 'wb'
    logging.debug('Choosing mirror ...')
    file_size = -1

    # urllib can be verbose
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    mirror = get_mirror(urls)
    url, ping_ms = mirror.url, mirror.elapsed.microseconds/1000

    logging.debug('Picked {} ping={}ms'.format(url, ping_ms))

    try:
        logging.debug('Starting download at %.1fMB' % (first_byte / 1e6))

        head = requests.head(url)
        file_size = int(head.headers['Content-length'])

        logging.debug('File size is %.1fMB' % (file_size / 1e6))
        headers = {"Range": "bytes=%s-" % first_byte}

        disp = tqdm.tqdm(total=file_size / 1e6, desc='Download: {}'.format(url), unit='MB', )
        disp.update(first_byte / 1e6)
        r = requests.get(url, headers=headers, stream=True, timeout=timeout)
        with open(tmp_file_path, file_mode) as f:
            for chunk in r.iter_content(chunk_size=block_size):
                disp.update(block_size / 1e6)
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
    except (IOError, TypeError, KeyError) as e:
        logging.error('Error - %s' % e)
        logging.error('Header from download attempt of {}: {}'.format(url, head.headers))
        raise e
    finally:
        # rename the temp download file to the correct name if fully downloaded
        if file_size == os.path.getsize(tmp_file_path):
            # if there's a hash value, validate the file
            if hash and not validate_file(tmp_file_path, hash):
                raise Exception('Error validating the file against its MD5 hash')
            shutil.move(tmp_file_path, file_path)
        elif file_size == -1:
            raise Exception('Error getting Content-Length from server: %s' % url)


class OrderedJobStreamer(threading.Thread):
    def __init__(self,
                 job: Callable,
                 job_args: list,
                 output_queue: queue.Queue,
                 executor=concurrent.futures.ProcessPoolExecutor,
                 max_workers: int = None):
        """Creates a thread pool to run a ordered list of jobs, enqueueing their results to a target queue.

        Args:
            job (Callable): The job to be run in batch
            job_args (list): The arguments for the job.
            output_queue (queue.Queue): The output_queue.
            executor ([type], optional): The executor. Defaults to concurrent.futures.ProcessPoolExecutor.
            max_workers ([int], optional): How many workers to spin up
        """
        super().__init__(target=self._ordered_job_streamer, daemon=True)
        self.job = job
        self.job_args = job_args
        self.output_queue = output_queue
        self._should_exit = False
        self.executor = executor
        self.max_workers = max_workers

    def _ordered_job_streamer(self):

        
        ex = self.executor(self.max_workers)

        def end_processes():
            if ex is not None:
                if ex._processes is not None:
                    for process in  ex._processes.values():
                        try:
                            process.kill()
                        except:
                            print("couldn;t kill process")
                            pass
                ex.shutdown(wait=False)
        atexit.register(end_processes)

        try:
            results = queue.Queue()
            # Enqueue jobs
            for arg in tqdm.tqdm(self.job_args):
                results.put(ex.submit(self.job, arg))

            # Dequeu jobs and push them to a queue.
            while not results.empty() and not self._should_exit:
                future = results.get()
                if future.exception():
                    raise future.exception()
                res = future.result()

                while not self._should_exit:
                    try:
                        self.output_queue.put(res, block=True, timeout=1)
                        break
                    except queue.Full:
                        pass
                        
            return
        except Exception:
            # abort workers immediately if anything goes wrong
            for process in ex._processes.values():
                process.kill()
            
            raise
        finally:
            ex.shutdown(wait=False)



    def shutdown(self):
        self._should_exit = True


def cat(*args):
    return np.concatenate(args)


def stack(*args):
    return np.stack(args)


def minibatch_gen(traj_iter, batch_size, nsteps):
    """
    generate ordered sequence of minibatches from trajectories.
    That is, minibatches start at the beginnging of trajectory and 
    go until the end, at which point a trajectory is replaced by a randomly
    chosen one. For instance, if S<nt> stands for timestep t in a trajectory n, 
    and F<nt> stands for final state in a trajectory , batch size is 2, and 
    nsteps is 4, then a sequence of minibatches can be:
    
    1.                    2.                  3.
       S11 S12 F13 S31      S32 S33 S34 S35      S36 S37 F38 S51
       S21 S22 S23 S24      S25 F26 S41 S42      S43 F44 S61 S71
    
    (in the example, the trajectories are ordered for clarity, but 
    they don't have to be)
    Used for behavior cloning with stateful models.
    This is roughly a batched version of minerl sarsd_iter
    
    Arguments:
        traj_iter  : iterator that generates one full trajectory at a time
        batch_size : int, size of the minibatch (number of parallel trajectories in the batch)
        nsteps     : int, number of timesteps in the minibatch
    
    Returns:
        iterator that generates minibatches as described above
    """
    try:
        # A rolling buffer of trajectories.
        trajs = [next(iter(traj_iter)) for _ in range(batch_size)]
        while True:
            rettraj = []
            for i, t in enumerate(trajs):
                # Flatten and condense trajectories
                while len(t['obs']['pov']) < nsteps:
                    trajs[i] = t = multimap(cat, *[t, next(traj_iter)])
                # Truncate trajectory to the nsteps.
                outtraj = (multimap(lambda x: x[:nsteps], t))

                # Shorten the trajectory.
                trajs[i] = multimap(lambda x: x[nsteps:], t)

                rettraj.append(outtraj)
            # Yield a batch.
            yield multimap(stack, *rettraj)
    except StopIteration:
        return
