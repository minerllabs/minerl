from minerl.data.data_pipeline import DataPipeline
from minerl.data.downloader import download
import os


def init(data_dir, num_workers=2, woker_batch_size=32, minimum_size_to_dequeue=32):
    d = DataPipeline(
        data_dir,
        num_workers,
        woker_batch_size,
        minimum_size_to_dequeue)
    return d


def reset():
    pass


def filter(fn):
    pass


def sample():
    return 'the best data'
    pass


def batch():
    pass

if __name__ == '__main__':
    init()