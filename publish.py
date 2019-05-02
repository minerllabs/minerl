"""
render.py
# This script renders the merged experiments into
# actions and videos by doing the following
# 1) Unzipping various mcprs and building render directories
#    containing meta data.
# 2) Running the action_rendering scripts
# 3) Running the video_rendering scripts
"""
import functools
import multiprocessing
import os
import sys
import time
import numpy
import tqdm
import shutil
import numpy as np
import random

#######################
### UTILITIES
#######################
J = os.path.join
E = os.path.exists
EXP_MIN_LEN_TICKS = 20 * 15  # 15 sec
WORKING_DIR = os.path.abspath("./output")
DATA_DIR = J(WORKING_DIR, "data_new")

RENDER_DIR = J(WORKING_DIR, "rendered_new")
BLACKLIST_PATH = J(WORKING_DIR, "blacklist.txt")

ACTION_FILE = "actions.tmcpr"
BAD_MARKER_NAME, GOOD_MARKER_NAME = 'INVALID', 'VALID'

METADATA_FILES = [
    'metaData.json',
    'markers.json',
    'mods.json',
    'stream_meta_data.json']

FAILED_COMMANDS = []

def touch(path):
    with open(path, 'w'):
        pass


def remove(path):
    if E(path):
        os.remove(path)


class ThreadManager(object):
    def __init__(self, man, num_workers, first_index, max_load):
        self.max_load = max_load
        self.first_index = first_index
        self.workers = man.list([0 for _ in range(num_workers)])
        self.worker_lock = man.Lock()

    def get_index(self):
        while True:
            with self.worker_lock:
                load = min(self.workers)
                if load < self.max_load:
                    index = self.workers.index(load)
                    self.workers[index] += 1
                    # print('Load is {} incrementing {}'.format(load, index))
                    # print(self.gpu_workers)
                    return index + self.first_index
                else:
                    time.sleep(0.01)

    def free_index(self, i):
        with self.worker_lock:
            self.workers[i - self.first_index] -= 1


##################
### PIPELINE
#################

# 1. Construct data working dirs.
def construct_data_dirs(blacklist):
    """
    Constructs the render directories omitting
    elements on a blacklist.
    """
    if not E(DATA_DIR):
        os.makedirs(DATA_DIR)

    data_dirs = []
    for experiemnt_folder in tqdm.tqdm(next(os.walk(DATA_DIR))[1], desc='Directories', position=0):
        for experiment_dir in tqdm.tqdm(next(os.walk(J(DATA_DIR, experiemnt_folder)))[1], desc='Experiments', position=1):
            data_dirs.append((experiment_dir, experiemnt_folder))
            # time.sleep(0.001)
    print()
    return data_dirs


def _render_data(output_root, manager, input):
    n = manager.get_index()
    recording_dir, experiment_folder = input
    ret = render_data(output_root, recording_dir, experiment_folder, lineNum=n)
    manager.free_index(n)
    return ret

# 2. render numpy format
def render_data(output_root, recording_dir, experiment_folder, lineNum=None):
    # Script to to pair actions with video recording
    # All times are in ms and we assume a actions list, a timestamp file, and a dis-syncronous mp4 video

    # Generate Numpy
    source_folder = J(DATA_DIR, experiment_folder, recording_dir)
    recording_source = J(source_folder, 'recording.mp4')
    universal_source = J(source_folder, 'univ.json')
    dest_folder = J(output_root, experiment_folder, recording_dir)
    recording_dest = J(dest_folder, 'recording.mp4')
    rendered_dest = J(dest_folder, 'rendered.npz')

    # Don't render again, ensure source exits
    if E(rendered_dest):
        # TODO check universal_source exists
        return 0

    # Don't render if files are missing
    if not E(source_folder) or not E(recording_source) or not E(universal_source):
        tqdm.tqdm.write('Files missing in ' + source_folder)
        return 0

    # Setup destination root
    if not E(dest_folder):
        try:
            os.makedirs(os.path.dirname(dest_folder))
        except OSError as exc:
            pass

    video_length = random.randint(6000, 150000)
    info = dict()
    info['mini_map'] = np.ones([video_length, 4, 4])
    info['health'] = np.ones([video_length, 1])
    info['inventory'] = np.ones([video_length, 10])
    info['current_item'] = np.ones([video_length, 1])
    np.save(rendered_dest, info)

    # vector = np.ones([video_length, 42])
    # np.save(rendered_dest, vector)

    # Copy video if necessary
    if not E(recording_dest):
        shutil.copyfile(recording_source, recording_dest)

    return 1


def main():
    """
    The main render script.
    """

    # 1. Load the blacklist.
    blacklist = set(numpy.loadtxt(BLACKLIST_PATH, dtype=numpy.str).tolist())

    print("Constructing data directory.")
    valid_data = construct_data_dirs(blacklist)

    print("Rendering videos: ")
    numSegments = []
    if E('errors.txt'):
        os.remove('errors.txt')
    try:
        numW = int(sys.argv[1]) if len(sys.argv) > 1 else 2

        multiprocessing.freeze_support()
        with multiprocessing.Pool(numW, initializer=tqdm.tqdm.set_lock, initargs=(multiprocessing.RLock(),)) as pool:
            manager = ThreadManager(multiprocessing.Manager(), numW, 1, 1)
            func = functools.partial(_render_data, DATA_DIR, manager)
            numSegments = list(
                tqdm.tqdm(pool.imap_unordered(func, valid_data), total=len(valid_data), desc='Files', miniters=1,
                          position=0, maxinterval=1))

            # for recording_name, render_path in tqdm.tqdm(valid_renders, desc='Files'):
            #     numSegmentsRendered += gen_sarsa_pairs(render_path, recording_name, DATA_DIR)
    except Exception as e:
        print('\n' * numW)
        print("Exception in pool: ", type(e),  e)
        print('Vectorized {} files in total!'.format(sum(numSegments)))
        if E('errors.txt'):
            print('Errors:')
            print(open('errors.txt', 'r').read())
        return

    numSegmentsRendered = sum(numSegments)

    print('\n' * numW)
    print('Vectorized {} files in total!'.format(numSegmentsRendered))
    if E('errors.txt'):
        print('Errors:')
        print(open('errors.txt', 'r').read())

if __name__ == "__main__":
    main()
