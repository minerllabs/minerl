from minerl.data.data_pipeline import DataPipeline
from minerl.data.download import download
import os


def make(environment, data_dir=None, num_workers=4, worker_batch_size=32, minimum_size_to_dequeue=32, force_download=False):
    """
    This is a thing that does stuff

    Raises:
        FileNotFoundError: [description]
        ValueError: [description]
        NotImplementedError: [description]
        NotImplementedError: [description]
        NotImplementedError: [description]

    Returns:
        [type]: [description]
    """
    # Ensure path is setup
    if data_dir is None and 'MINERL_DATA_ROOT' in os.environ:
        data_dir = os.environ['MINERL_DATA_ROOT']
    elif data_dir is not None and not os.path.exists(data_dir):
        if force_download:
            print("Provided data directory does not exist: ", data_dir)
            data_dir = download(data_dir)
        else:
            raise FileNotFoundError("Provided data directory does not exist. "
                                    "Specify force_download=True to download default dataset")
    else:
        if force_download:
            print("Provided data directory does not exist: ", data_dir)
            data_dir = download(data_dir)
        else:
            raise ValueError("No data_dir provided and $MINERL_DATA_ROOT undefined."
                             "Specify force_download=True to download default dataset")

    d = DataPipeline(
        os.path.join(data_dir, environment),
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
