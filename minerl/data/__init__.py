from minerl.data.data_pipeline import DataPipeline
from minerl.data import download
import os


def init(data_dir=None, num_workers=1, woker_batch_size=32, minimum_size_to_dequeue=32):
    if data_dir is None and 'MINERL_DATA_ROOT' in os.environ:
        data_dir = os.environ['MINERL_DATA_ROOT']
    elif not os.path.exists(data_dir):
        raise FileNotFoundError("Provided data directory does not exist")
    else:
        raise ValueError("No data_dir provided and $MINERL_DATA_ROOT undefined")
    d = DataPipeline(
        data_dir,
        num_workers,
        woker_batch_size,
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
