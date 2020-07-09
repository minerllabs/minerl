import os
import urllib.request, urllib.error, urllib.parse
import time

from . import utils

def download(url, dest, requestArgs=None, startByte=0, endByte=None, timeout=4, shared_var=None, thread_shared_cmds=None, logger=None, retries=3):
    "The basic download function that runs at each thread."
    logger = logger or utils.DummyLogger()
    req = urllib.request.Request(url, **requestArgs)
    if endByte:
        req.add_header('Range', 'bytes={:.0f}-{:.0f}'.format(startByte, endByte))
    logger.info("Downloading '{}' to '{}'...".format(url, dest))
    try:
        urlObj = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        if e.code == 416:
            '''
            HTTP 416 Error: Requested Range Not Satisfiable. Happens when we ask
            for a range that is not available on the server. It will happen when
            the server will try to send us a .html page that means something like
            "you opened too many connections to our server". If this happens, we
            will wait for the other threads to finish their connections and try again.
            '''
            
            if retries > 0:
                logger.warning("Thread didn't got the file it was expecting. Retrying ({} times left)...".format(retries-1))
                time.sleep(5)
                return download(url, dest, requestArgs, startByte, endByte, timeout, shared_var, thread_shared_cmds, logger, retries-1)
            else:
                raise
        else:
            raise
    
    with open(dest, 'wb') as f:
        if endByte:
            filesize = endByte-startByte
        else:
            try:
                meta = urlObj.info()
                filesize = int(urlObj.headers["Content-Length"])
                logger.info("Content-Length is {}.".format(filesize))
            except (IndexError, KeyError, TypeError):
                logger.warning("Server did not send Content-Length. Filesize is unknown.")
        
        filesize_dl = 0  # total downloaded size
        limitspeed_timestamp = time.time()
        limitspeed_filesize = 0
        block_sz = 8192
        while True:
            if thread_shared_cmds:
                if 'stop' in thread_shared_cmds:
                    logger.info('stop command received. Stopping.')
                    raise CanceledException()
                if 'pause' in thread_shared_cmds:
                    time.sleep(0.2)
                    continue
                if 'limit' in thread_shared_cmds:
                    now = time.time()
                    time_passed = now - limitspeed_timestamp
                    if time_passed > 0.1:  # we only observe the limit after 100ms
                        # if we passed the limit, we should
                        if (filesize_dl-limitspeed_filesize)/time_passed >= thread_shared_cmds['limit']:
                            time_to_sleep = (filesize_dl-limitspeed_filesize) / thread_shared_cmds['limit']
                            logger.debug('Thread has downloaded {} in {}. Limit is {}/s. Slowing down...'.format(utils.sizeof_human(filesize_dl-limitspeed_filesize), utils.time_human(time_passed, fmt_short=True, show_ms=True), utils.sizeof_human(thread_shared_cmds['limit'])))
                            time.sleep(time_to_sleep)
                            continue
                        else:
                            limitspeed_timestamp = now
                            limitspeed_filesize = filesize_dl
                
            try:
                buff = urlObj.read(block_sz)
            except Exception as e:
                logger.error(str(e))
                if shared_var:
                    shared_var.value -= filesize_dl
                raise
                
            if not buff:
                break

            filesize_dl += len(buff)
            if shared_var:
                shared_var.value += len(buff)
            f.write(buff)
            
    urlObj.close()
