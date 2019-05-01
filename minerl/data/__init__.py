from minerl.data.data_pipeline import DataPipeline
from minerl.data.downloader import download
import os


def init():
    d = DataPipeline(os.path.join('C:', 'data', 'data_texture_1_low_res'), 256, 32, 32)
    for batch in d.batch_iter(64, 64):
        print(batch)
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