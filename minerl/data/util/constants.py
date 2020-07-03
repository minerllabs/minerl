import os
import sys
import time
from os.path import join as J


def we_are_frozen():
    # All of the modules are built-in to the interpreter, e.g., by py2exe
    return hasattr(sys, "frozen")


def module_path():
    encoding = sys.getfilesystemencoding()
    if we_are_frozen():
        return os.path.dirname((sys.executable))
    return os.path.dirname((__file__))


ASSETS_DIR = os.path.abspath(J(os.path.dirname(__file__), '..', 'assets'))

J = os.path.join
E = os.path.exists

BASE_DIR = os.environ.get('MINERL_OUTPUT_ROOT', os.path.expanduser(
    J('~', 'minerl.data')
))

RENDERERS_DIR = os.path.expanduser(
    J('~', 'renderers'))
NUM_MINECRAFTS = 28

OUTPUT_DIR = J(BASE_DIR, 'output')
DOWNLOAD_DIR = J(BASE_DIR, 'downloaded_sync')
BUCKET_NAME = 'pizza-party'

# MERGING
MERGED_DIR = J(OUTPUT_DIR, 'merged')
BLACKLIST_TXT = J(OUTPUT_DIR, 'blacklist.txt')
PARSE_COMMAND = [os.path.abspath(J(os.path.dirname((__file__)), '..', 'pipeline', 'parser', 'parse')), '-f']
Z7_COMMAND = ["7z"]
TEMP_ROOT = J(BASE_DIR, 'tmp')
BLOCK_SIZE = 1024 * 1024
ACTION_FILE = 'actions.tmcpr'
RECORDING_FILE = 'recording.tmcpr'
TEMP_FILE = 'tmp.tmcpr'
GLOB_STR_BASE = J(DOWNLOAD_DIR, "*", "*", "*", "*")

#### RENDERING

RENDER_DIR = J(OUTPUT_DIR, "rendered")
MINECRAFT_DIR = [J(RENDERERS_DIR, 'minecraft_{}'.format(i)) for i in range(NUM_MINECRAFTS)]
RECORDING_PATH = [J(d, 'replay_recordings') for d in MINECRAFT_DIR]
RENDERED_VIDEO_PATH = [J(d, 'replay_videos') for d in MINECRAFT_DIR]
RENDERED_LOG_PATH = [J(d, 'replay_logs') for d in MINECRAFT_DIR]
FINISHED_FILE = [J(d, 'finished.txt') for d in MINECRAFT_DIR]
LOG_FILE = [J(d, 'logs', 'debug.log') for d in MINECRAFT_DIR]
MC_LAUNCHER = [('bash', J(d, 'launch.sh')) for d in MINECRAFT_DIR]
RENDER_ONLY_EXPERIMENTS = ['o_dia', 'survivaltreechop', 'navigate', 'navigateextreme', 'o_iron', 'none']

# Error directories
ERROR_PARENT_DIR = J(OUTPUT_DIR, 'error_logs')
EOF_EXCEP_DIR = J(ERROR_PARENT_DIR, 'end_of_file_reached')
ZEROLEN_DIR = J(ERROR_PARENT_DIR, 'zero_length')
NULL_PTR_EXCEP_DIR = J(ERROR_PARENT_DIR, 'null_pointer_except')
ZIP_ERROR_DIR = J(ERROR_PARENT_DIR, 'zip_file')
MISSING_RENDER_OUTPUT = J(ERROR_PARENT_DIR, 'missing_output')
OTHER_ERROR_DIR = J(ERROR_PARENT_DIR, 'other')
X11_ERROR_DIR = J(ERROR_PARENT_DIR, 'x11_error')

# metadata decomp

END_OF_STREAM = 'end_of_stream.txt'
ACTION_FILE = "actions.tmcpr"
BAD_MARKER_NAME, GOOD_MARKER_NAME = 'INVALID', 'VALID'
SKIPPED_RENDER_FLAG = 'SKIPPED_RENDER'

METADATA_FILES = [
    'metaData.json',
    'markers.json',
    'mods.json',
    'stream_meta_data.json']

# generation

DATA_DIR = J(OUTPUT_DIR, 'data')
EXP_MIN_LEN_TICKS = 20 * 15  # 15 sec
FAILED_COMMANDS = []
GENERATE_VERSION = '1'


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
            try:
                with self.worker_lock:
                    load = min(self.workers)
                    if load < self.max_load:
                        index = self.workers.index(load)  # Error -> None.
                        if index is not None:
                            self.workers[index] += 1
                            # print('Load is {} incrementing {}'.format(load, index))
                            return index + self.first_index
                    else:
                        time.sleep(0.01)
            except:
                pass

    def free_index(self, i):
        with self.worker_lock:
            self.workers[i - self.first_index] -= 1
