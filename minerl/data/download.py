import os
from urllib.error import URLError
from urllib.error import HTTPError

import requests
import shutil
import tarfile
import minerl
import time
import tqdm
from threading import Thread


from minerl.dependencies.pySmartDL import pySmartDL

import logging

from minerl.data.version import VERSION_FILE_NAME, DATA_VERSION, assert_version

logger = logging.getLogger(__name__)


def download(directory=None, resolution='low', texture_pack=0, update_environment_variables=True, disable_cache=False,
             experiment=None, minimal=False):
    """Downloads MineRLv0 to specified directory. If directory is None, attempts to 
    download to $MINERL_DATA_ROOT. Raises ValueError if both are undefined.
    
    Args:
        directory (os.path): destination root for downloading MineRLv0 datasets
        resolution (str, optional): one of [ 'low', 'high' ] corresponding to video resolutions of [ 64x64, 256,128 ]
            respectively (note: high resolution is not currently supported). Defaults to 'low'.
        texture_pack (int, optional): 0: default Minecraft texture pack, 1: flat semi-realistic texture pack. Defaults
            to 0.
        update_environment_variables (bool, optional): enables / disables exporting of MINERL_DATA_ROOT environment
            variable (note: for some os this is only for the current shell) Defaults to True.
        disable_cache (bool, optional): downloads temporary files to local directory. Defaults to False
        experiment (str, optional): specify the desired experiment to download. Will only download data for this
            experiment. Note there is no hash verification for individual experiments
        minimal (bool, optional): download a minimal version of the dataset
    """
    if directory is None:
        if 'MINERL_DATA_ROOT' in os.environ and len(os.environ['MINERL_DATA_ROOT']) > 0:
            directory = os.environ['MINERL_DATA_ROOT']
        else:
            raise ValueError("Provided directory is None and $MINERL_DATA_ROOT is not defined")
    elif update_environment_variables:
        os.environ['MINERL_DATA_ROOT'] = os.path.expanduser(
            os.path.expandvars(os.path.normpath(directory)))

    if experiment is not None:
        logger.info("Downloading experiment {} to {}".format(experiment, directory))
    else:
        logger.info("Downloading dataset to {}".format(directory))

    if os.path.exists(directory):
        try:
            assert_version(directory)
        except RuntimeError as r:
            if r.comparison == "less":
                raise r
            logger.error(str(r))
            logger.error("Deleting existing data and forcing a data update!")
            try:
                shutil.rmtree(directory)
            except Exception as e:
                logger.error("Could not delete {}. Do you have permission?".format(directory))
                raise e
            try:
                os.makedirs(directory)
            except:
                pass

    download_path = os.path.join(directory, '') if disable_cache else None
    mirrors = ["https://router.sneakywines.me/"] #, "https://router2.sneakywines.me/"]

    if experiment is None:
        min_str = '_minimal' if minimal else ''
        filename = "minerl-v{}/data_texture_{}_{}_res{}.tar.gz".format(DATA_VERSION, texture_pack, resolution, min_str)
        urls = [mirror + filename for mirror in mirrors]

        obj = pySmartDL.SmartDL(urls, progress_bar=True, logger=logger, dest=download_path, threads=20, timeout=60)
    else:
        # Check if experiment is already downloaded
        if os.path.exists(os.path.join(directory, experiment)):
            logger.warning("{} exists - skipping re-download!".format(os.path.join(directory, experiment)))
            return directory
        filename = "minerl-v{}/{}.tar.gz".format(DATA_VERSION, experiment)
        urls = [mirror + filename for mirror in mirrors]
        obj = pySmartDL.SmartDL(urls, progress_bar=True, logger=logger, dest=download_path, threads=20, timeout=60)
    try:
        logger.info("Fetching download hash ...")
        obj.fetch_hash_sums()
        logger.info("Starting download ...")
        obj.start()
    except pySmartDL.HashFailedException:
        logger.error("Hash check failed! Is server under maintenance??")
        logger.error("URL {}".format(obj.url))
        return None
    except pySmartDL.CanceledException:
        logger.error("Download canceled by user")
        return None
    except HTTPError as e:
        logger.error("HTTP error encountered when downloading")
        if experiment is not None:
            logger.error("is {}  a valid minerl environment?".format(experiment))
        logger.error(e.errno)
        return None
    except URLError as e:
        logger.error("URL error encountered when downloading - please try again")
        logger.error(e.errno)
        return None
    except TimeoutError as e:
        logger.error("Timeout encountered when downloading - is your connection stable")
        logger.error(e.errno)
        return None
    except IOError as e:
        logger.error("IO error encountered when downloading - please try again")
        logger.error(e.errno)
        return None

    logging.info('Success - downloaded {}'.format(obj.get_dest()))

    logging.info('Extracting downloaded files - this may take some time')
    with tarfile.open(obj.get_dest(), mode="r:*") as tf:
        t = Thread(target=tf.extractall(path=directory))
        t.start()
        while t.isAlive():
            time.sleep(5)
            logging.info('.', end='')

        logging.info('Success - extracted files to {}'.format(directory))

    if disable_cache:
        logging.info('Deleting cached tar file')
        os.remove(obj.get_dest())

    try:
        assert_version(directory)
    except RuntimeError as r:
        logger.error(str(r))

    return directory
