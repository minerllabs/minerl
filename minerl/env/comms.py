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

import struct
import socket
import functools
import time
import logging
import Pyro4

logger = logging.getLogger(__name__)

retry_count = 20
retry_timeout = 10


def retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        retry_exc = None
        for i in range(retry_count):
            try:
                return func(*args, **kwargs)
            except Pyro4.errors.PyroError as e: 
                logger.error("An error occurred contacting the instance manager. Is it started!?")
                raise e
            except Exception as e:
                if retry_exc is None:
                    retry_exc = e
                if i < retry_count - 1:
                    logger.debug("Pause before retry on " + str(e))
                    # raise e
                    time.sleep(retry_timeout)
                    logger.debug("Pause complete.")
        raise retry_exc
    return wrapper


def send_message(sock, data):
    length = len(data)
    sock.sendall(struct.pack('!I', length))
    sock.sendall(data)


def recv_message(sock):
    lengthbuf = recvall(sock, 4)
    if not lengthbuf:
        return None
    length, = struct.unpack('!I', lengthbuf)
    return recvall(sock, length)


def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf


class QueueLogger(logging.StreamHandler):
    def __init__(self, queue):
        self._queue = queue
        return super().__init__(None)
    
    def flush(self):
        pass

    
    def emit(self, record):
        self._queue.append((self.level, record))

