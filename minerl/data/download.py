import os
import requests
import tqdm


def download(directory: os.path, resolution: str = 'low', texture_pack: int = 1, update_enviroment_variables=True) -> None:
    """
    Downloads MineRLv0 to specified directory. If directory is None downloads to $MINERL_DATA_ROOT. Throws error if both
    are not defined.
    :param update_enviroment_variables: Enables / disables setting of MineRL environment variables
    :type update_enviroment_variables:
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
    elif update_enviroment_variables:
        os.environ['MINERL_DATA_ROOT'] = directory

    # TODO pull JSON defining dataset URLS from webserver instead of hard-coding
    url = "https://router.sneakywines.me/minerl/data_texture_{}_{}_res.tar.gz".format(texture_pack, resolution)

    response = requests.get(url, stream=True)

    with open(directory, "wb") as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)
    pass
