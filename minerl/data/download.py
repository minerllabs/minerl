import os
import requests
import tqdm
import tarfile
import pySmartDL


def download(directory: os.path, resolution: str = 'low', texture_pack: int = 0, update_environment_variables=True):
    """
    Downloads MineRLv0 to specified directory. If directory is None downloads to $MINERL_DATA_ROOT. Throws error if both
    are not defined.
    :param update_environment_variables: Enables / disables setting of MineRL environment variables
    :type update_environment_variables:
    :param directory: Destination for downloading MineRLv0 datasets
    :type directory:
    :param resolution: One of [ 'low', 'high' ] corresponding to video resolutions of [ 64x64, 256,128 ] respectively
    :type resolution:
    :param texture_pack: 0: Default Minecraft texture pack, 1: custom flat semi-realistic texture pack
    :type texture_pack:
    """
    if directory is None:
        if 'MINERL_DATA_ROOT' in os.environ and len(os.environ['MINERL_DATA_ROOT']) > 0:
            directory = os.environ['MINERL_DATA_ROOT']
        else:
            raise ValueError("Provided directory is None and $MINERL_DATA_ROOT is not defined")
    elif update_environment_variables:
        os.environ['MINERL_DATA_ROOT'] = os.path.normpath(directory)

    # TODO pull JSON defining dataset URLS from webserver instead of hard-coding
    # TODO add hashed to website to verify downloads for mirrors
    filename, hashname = "data_texture_{}_{}_res.tar.gz".format(texture_pack, resolution), \
                     "data_texture_{}_{}_res.md5".format(texture_pack, resolution)
    url = "https://router.sneakywines.me/minerl/" + filename
    hash_url = "https://router.sneakywines.me/minerl/" + hashname

    response = requests.get(url, stream=True)

    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(os.path.join(directory, filename), "wb") as handle:
        for data in tqdm.tqdm(response.iter_content(chunk_size=1048576)):
            handle.write(data)

    response = requests.get(hash_url)
    md5_hash = response.text

    obj = pySmartDL.SmartDL(url, progress_bar=True, connect_default_logger=True)
    obj.add_hash_verification('md5', md5_hash)
    try:
        obj.start()
    except pySmartDL.HashFailedException:
        print("Hash check failed!")
    except pySmartDL.CanceledException:
        print("Download canceled by user")
    finally:
        tf = tarfile.open(obj.get_dest())
        tf.extractall()

    return directory
