import os
import requests
import tqdm
import tarfile
import pySmartDL
import logging


def download(directory: os.path, resolution: str = 'low', texture_pack: int = 0, update_environment_variables=True):
    """Downloads MineRLv0 to specified directory. If directory is None, attempts to 
    download to $MINERL_DATA_ROOT. Raises ValueError if both are undefined.
    
    Args:
        directory (os.path): destination root for downloading MineRLv0 datasets
        resolution (str, optional): one of [ 'low', 'high' ] corresponding to video resolutions of [ 64x64, 256,128 ] respectively (note: high resolution is not currently supported). Defaults to 'low'.
        texture_pack (int, optional): 0: default Minecraft texture pack, 1: flat semi-realistic texture pack. Defaults to 0.
        update_environment_variables (bool, optional): enables / disables exporting of MINERL_DATA_ROOT environment variable (note: for some os this is only for the current shell) Defaults to True.
    """
    if directory is None:
        if 'MINERL_DATA_ROOT' in os.environ and len(os.environ['MINERL_DATA_ROOT']) > 0:
            directory = os.environ['MINERL_DATA_ROOT']
        else:
            raise ValueError("Provided directory is None and $MINERL_DATA_ROOT is not defined")
    elif update_environment_variables:
        os.environ['MINERL_DATA_ROOT'] = os.path.expanduser(
            os.path.expandvars(os.path.normpath(directory)))

    # TODO pull JSON defining dataset URLS from webserver instead of hard-coding
    # TODO add hashed to website to verify downloads for mirrors
    filename, hashname = "data_texture_{}_{}_res.tar.gz".format(texture_pack, resolution), \
                     "data_texture_{}_{}_res.md5".format(texture_pack, resolution)
    urls = ["https://router.sneakywines.me/minerl/" + filename]
    hash_url = "https://router.sneakywines.me/minerl/" + hashname

    response = requests.get(hash_url)
    md5_hash = response.text

    obj = pySmartDL.SmartDL(urls, progress_bar=True, logger=logging.getLogger(__name__))
    obj.add_hash_verification('md5', md5_hash)
    try:
        obj.start()
    except pySmartDL.HashFailedException:
        print("Hash check failed!")
    except pySmartDL.CanceledException:
        print("Download canceled by user")
    finally:
        logging.info('Extracting downloaded files ... ')
        tf = tarfile.open(obj.get_dest(), mode="r:*")
        tf.extractall(path=directory)

    return directory
