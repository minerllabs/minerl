import os.path
import requests
import shutil
import hashlib
import logging
import tqdm

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
            chunk = f.read(1000 * 1000) # 1MB
            if not chunk:
                break
            m.update(chunk)
    return m.hexdigest() == hash

def download_with_resume(url, file_path, hash=None, timeout=10):
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
    block_size = 1000 * 1000 # 1MB
    tmp_file_path = file_path + '.part'
    first_byte = os.path.getsize(tmp_file_path) if os.path.exists(tmp_file_path) else 0
    file_mode = 'ab' if first_byte else 'wb'
    logging.debug('Starting download at %.1fMB' % (first_byte / 1e6))
    file_size = -1
    try:
        head= requests.head(url)
        file_size = int(head.headers['Content-length'])

        logging.debug('File size is %s' % file_size)
        headers = {"Range": "bytes=%s-" % first_byte}

        disp = tqdm.tqdm(total=file_size /1e6, desc=f'Download: {url}',unit='MB', )
        disp.update(first_byte /1e6)
        r = requests.get(url, headers=headers, stream=True, timeout=timeout)
        with open(tmp_file_path, file_mode) as f:
            for chunk in r.iter_content(chunk_size=block_size): 
                disp.update(block_size / 1e6)
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
    except (IOError, TypeError, KeyError) as e:
        logging.error('Error - %s' % e)
        logging.error(f'Header from download attempt of {url}: {head.headers}')
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


if __name__ == '__main__':
    download_with_resume('https://minerl.s3.amazonaws.com/v2/data_texture_0_low_res.tar.gz', '/tmp/asd')    