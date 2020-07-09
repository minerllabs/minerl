# -*- coding: utf-8 -*-
'''
The Utils class contains many functions for project-wide use.
'''

import os
import sys
import urllib.request, urllib.parse, urllib.error
import random
import logging
import re
import hashlib
from concurrent import futures
from math import log, ceil
import shutil

DEFAULT_LOGGER_CREATED = False

def combine_files(parts, dest, chunkSize = 1024 * 1024 * 4):
	'''
	Combines files.

	:param parts: Source files.
	:type parts: list of strings
	:param dest: Destination file.
	:type dest: string
    :param chunkSize: Fetching chunk size.
	:type chunkSize: int

	'''
	if len(parts) == 1:
		shutil.move(parts[0], dest)
	else:
		with open(dest, 'wb') as output:
			for part in parts:
				with open(part, 'rb') as input:
					data = input.read(chunkSize)
					while data:
						output.write(data)
						data = input.read(chunkSize)
				os.remove(part)
            
def url_fix(s, charset='utf-8'):
    '''
    Sometimes you get an URL by a user that just isn't a real
    URL because it contains unsafe characters like ' ' and so on.  This
    function can fix some of the problems in a similar way browsers
    handle data entered by the user:

    >>> url_fix(u'http://de.wikipedia.org/wiki/Elf (Begriffsklärung)')
    'http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29'

    :param s: Url address.
    :type s: string
    :param charset: The target charset for the URL if the url was
                    given as unicode string. Default is 'utf-8'.
    :type charset: string
    :rtype: string
                    
    (taken from `werkzeug.utils <http://werkzeug.pocoo.org/docs/utils/>`_)
    '''
    scheme, netloc, path, qs, anchor = urllib.parse.urlsplit(s)
    path = urllib.parse.quote(path, '/%')
    qs = urllib.parse.quote_plus(qs, ':&%=')
    return urllib.parse.urlunsplit((scheme, netloc, path, qs, anchor))
    
def progress_bar(progress, length=20):
    '''
    Returns a textual progress bar.
    
    >>> progress_bar(0.6)
    '[##########--------]'
    
    :param progress: Number between 0 and 1 describes the progress.
    :type progress: float
    :param length: The length of the progress bar in chars. Default is 20.
    :type length: int
    :rtype: string
    '''
    length -= 2  # The brackets are 2 chars long.
    if progress < 0:
        progress = 0
    if progress > 1:
        progress = 1
    return "[" + "#"*int(progress*length) + "-"*(length-int(progress*length)) + "]"
    
def is_HTTPRange_supported(url, timeout=15):
    '''
    Checks if a server allows `Byte serving <https://en.wikipedia.org/wiki/Byte_serving>`_,
    using the Range HTTP request header and the Accept-Ranges and Content-Range HTTP response headers.
    
    :param url: Url address.
    :type url: string
    :param timeout: Timeout in seconds. Default is 15.
    :type timeout: int
    :rtype: bool
    '''
    url = url.replace(' ', '%20')
    
    fullsize = get_filesize(url)
    if not fullsize:
        return False
    
    headers = {'Range': 'bytes=0-3'}
    req = urllib.request.Request(url, headers=headers)
    urlObj = urllib.request.urlopen(req, timeout=timeout)
    urlObj.close()
    
    if "Content-Length" not in urlObj.headers:
        return False

    filesize = int(urlObj.headers["Content-Length"])
    return filesize != fullsize

def get_filesize(url, timeout=15):
    '''
    Fetches file's size of a file over HTTP.
    
    :param url: Url address.
    :type url: string
    :param timeout: Timeout in seconds. Default is 15.
    :type timeout: int
    :returns: Size in bytes.
    :rtype: int
    '''
    try:
        urlObj = urllib.request.urlopen(url, timeout=timeout)
        file_size = int(urlObj.headers["Content-Length"])
    except (IndexError, KeyError, TypeError, urllib.error.HTTPError, urllib.error.URLError):
        return 0
        
    return file_size
    
def get_random_useragent():
    '''
    Returns a random popular user-agent.
    Taken from `here <http://techblog.willshouse.com/2012/01/03/most-common-user-agents/>`_, last updated on 2019/07/26.
    
    :returns: user-agent
    :rtype: string
    '''
    l = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:67.0) Gecko/20100101 Firefox/67.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
        'Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
	]
    return random.choice(l)

def sizeof_human(num):
    '''
    Human-readable formatting for filesizes. Taken from `here <http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size>`_.
    
    >>> sizeof_human(175799789)
    '167.7 MB'
    
    :param num: Size in bytes.
    :type num: int
    
    :rtype: string
    '''
    unit_list = list(zip(['B', 'kB', 'MB', 'GB', 'TB', 'PB'], [0, 0, 1, 2, 2, 2]))
    
    if num > 1:
        exponent = min(int(log(num, 1024)), len(unit_list) - 1)
        quotient = float(num) / 1024**exponent
        unit, num_decimals = unit_list[exponent]
        
        format_string = '{:,.%sf} {}' % (num_decimals)
        return format_string.format(quotient, unit)
            
    if num == 0:
        return '0 bytes'
    if num == 1:
        return '1 byte'

def time_human(duration, fmt_short=False, show_ms=False):
    '''
    Human-readable formatting for timing. Based on code from `here <http://stackoverflow.com/questions/6574329/how-can-i-produce-a-human-readable-difference-when-subtracting-two-unix-timestam>`_.
    
    >>> time_human(175799789)
    '6 years, 2 weeks, 4 days, 17 hours, 16 minutes, 29 seconds'
    >>> time_human(589, fmt_short=True)
    '9m49s'
    
    :param duration: Duration in seconds.
    :type duration: int/float
    :param fmt_short: Format as a short string (`47s` instead of `47 seconds`)
    :type fmt_short: bool
    :param show_ms: Specify milliseconds in the string.
    :type show_ms: bool
    :rtype: string
    '''
    ms = int(duration % 1 * 1000)
    duration = int(duration)
    if duration == 0 and (not show_ms or ms == 0):
        return "0s" if fmt_short else "0 seconds"
            
    INTERVALS = [1, 60, 3600, 86400, 604800, 2419200, 29030400]
    if fmt_short:
        NAMES = ['s'*2, 'm'*2, 'h'*2, 'd'*2, 'w'*2, 'y'*2]
    else:
        NAMES = [
            ('second', 'seconds'),
            ('minute', 'minutes'),
            ('hour', 'hours'),
            ('day', 'days'),
            ('week', 'weeks'),
            ('month', 'months'),
            ('year', 'years')
        ]
    
    result = []
    
    for i in range(len(NAMES)-1, -1, -1):
        a = duration // INTERVALS[i]
        if a > 0:
            result.append( (a, NAMES[i][1 % a]) )
            duration -= a * INTERVALS[i]

    if show_ms and ms > 0:
        result.append((ms, "ms" if fmt_short else "milliseconds"))
    
    if fmt_short:
        return "".join(["%s%s" % x for x in result])
    return ", ".join(["%s %s" % x for x in result])

def get_file_hash(algorithm, path):
    '''
    Calculates a file's hash.

    .. WARNING::
        The hashing algorithm must be supported on your system, as documented at `hashlib documentation page <http://docs.python.org/3/library/hashlib.html>`_.
    
    :param algorithm: Hashing algorithm.
    :type algorithm: string
    :param path: The file path
    :type path: string
    :rtype: string
    '''
    hashAlg = hashlib.new(algorithm)
    block_sz = 1*1024**2  # 1 MB

    with open(path, 'rb') as f:
        data = f.read(block_sz)
        while data:
            hashAlg.update(data)
            data = f.read(block_sz)
    
    return hashAlg.hexdigest()

def calc_chunk_size(filesize, threads, minChunkFile):
    '''
    Calculates the byte chunks to download.
    
    :param filesize: filesize in bytes.
    :type filesize: int
    :param threads: Number of trheads
    :type threads: int
    :param minChunkFile: Minimum chunk size
    :type minChunkFile: int
    :rtype: Array of (startByte,endByte) tuples
    '''
    if not filesize:
        return [(0, 0)]
        
    while ceil(filesize/threads) < minChunkFile and threads > 1:
        threads -= 1
        
    args = []
    pos = 0
    chunk = ceil(filesize/threads)
    for i in range(threads):
        startByte = pos
        endByte = pos + chunk
        if endByte > filesize-1:
            endByte = filesize-1
        args.append((startByte, endByte))
        pos += chunk+1
        
    return args
    
def create_debugging_logger():
    '''
    Creates a debugging logger that prints to console.
    
    :rtype: `logging.Logger` instance
    '''
    global DEFAULT_LOGGER_CREATED

    t_log = logging.getLogger('pySmartDL')

    if not DEFAULT_LOGGER_CREATED:
        t_log.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter('[%(levelname)s||%(thread)d@{%(pathname)s:%(lineno)d}] %(message)s'))
        t_log.addHandler(console)
        DEFAULT_LOGGER_CREATED = True
    
    return t_log
    
class DummyLogger(object):
    '''
    A dummy logger. You can call `debug()`, `warning()`, etc on this object, and nothing will happen.
    '''
    def __init__(self):
        pass

    def dummy_func(self, *args, **kargs):
        pass

    def __getattr__(self, name):
        if name.startswith('__'):
            return object.__getattr__(name)
        return self.dummy_func
        
class ManagedThreadPoolExecutor(futures.ThreadPoolExecutor):
    '''
	Managed Thread Pool Executor. A subclass of ThreadPoolExecutor.
    '''
    def __init__(self, max_workers):
        futures.ThreadPoolExecutor.__init__(self, max_workers)
        self._futures = []
    
    def submit(self, fn, *args, **kwargs):
        future = super().submit(fn, *args, **kwargs)
        self._futures.append(future)
        return future
    
    def done(self):
        return all([x.done() for x in self._futures])
       
    def get_exceptions(self):
        '''
        Return all the exceptions raised.

        :rtype: List of `Exception` instances'''
        l = []
        for x in self._futures:
            if x.exception():
                l.append(x.exception())
        return l

    def get_exception(self):
        '''
        Returns only the first exception. Returns None if no exception was raised.

        :rtype: `Exception` instance
        '''
        for x in self._futures:
            if x.exception():
                return x.exception()
        return None
