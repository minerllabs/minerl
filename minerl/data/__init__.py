from minerl.data.data_pipeline import DataPipeline
from minerl.data.buffered_batch_iter import BufferedBatchIter
from minerl.data.download import download
import os

from minerl.data.version import DATA_VERSION, FILE_PREFIX, VERSION_FILE_NAME

import minerl.data.version


def make(environment=None, data_dir=None, num_workers=4, worker_batch_size=32, minimum_size_to_dequeue=32,
         force_download=False):
    """
    Initalizes the data loader with the chosen environment
    
    Args:
        environment (string): desired MineRL environment
        data_dir (string, optional): specify alternative dataset location. Defaults to None.
        num_workers (int, optional): number of files to load at once. Defaults to 4.
        force_download (bool, optional): specifies whether or not the data should be downloaded if missing. Defaults to False.

    Returns:
        DataPipeline: initalized data pipeline
    """

    # Ensure path is setup
    if data_dir is None and 'MINERL_DATA_ROOT' in os.environ:
        data_dir = os.environ['MINERL_DATA_ROOT']
    if data_dir is not None and not os.path.exists(data_dir):
        if force_download:
            print("Provided data directory does not exist: ", data_dir)
            data_dir = download(data_dir)
        else:
            raise FileNotFoundError("Provided data directory does not exist. "
                                    "Specify force_download=True to download default dataset")
    elif data_dir is None:
        if force_download:
            print("Provided data directory does not exist: ", data_dir)
            data_dir = download(data_dir)
        else:
            raise ValueError("No data_dir provided and $MINERL_DATA_ROOT undefined."
                             "Specify force_download=True to download default dataset")

    assert data_dir is not None, "data_dir is not provided, and download has failed"
    minerl.data.version.assert_version(data_dir)

    d = DataPipeline(
        os.path.join(data_dir, environment),
        environment,
        num_workers,
        worker_batch_size,
        minimum_size_to_dequeue)
    return d


def reset():
    raise NotImplementedError()


def filter_data(fn):
    raise NotImplementedError()
    pass


def sample():
    raise NotImplementedError()
    pass
