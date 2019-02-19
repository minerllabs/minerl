import os

# UTILITIES
#######################
import shutil

from tqdm import tqdm

J = os.path.join
E = os.path.exists
WORKING_DIR = "output"
MERGED_DIR = J(WORKING_DIR, "merged_new")
RENDER_DIR = J(WORKING_DIR, "rendered_new")
MINECRAFT_DIR = J('/', 'home', 'hero', 'minecraft')
RECORDING_PATH = J(MINECRAFT_DIR, 'replay_recordings')
RENDERED_VIDEO_PATH = J(MINECRAFT_DIR, 'replay_videos')
RENDERED_LOG_PATH  =  J(MINECRAFT_DIR,  'replay_logs')
FINISHED_FILE = J(MINECRAFT_DIR, 'finished.txt')
LOG_FILE = J(J(MINECRAFT_DIR, 'logs'), 'debug.log')  # RAH
#Error directories
ERROR_PARENT_DIR = J(WORKING_DIR, 'error_logs')
EOF_EXCEP_DIR = J(ERROR_PARENT_DIR, 'end_of_file_reached')
ZEROLEN_DIR = J(ERROR_PARENT_DIR, 'zero_length')
NULL_PTR_EXCEP_DIR = J(ERROR_PARENT_DIR, 'null_pointer_except')
ZIP_ERROR_DIR = J(ERROR_PARENT_DIR, 'zip_file')
MISSING_RENDER_OUTPUT = J(ERROR_PARENT_DIR, 'missing_output')

MC_LAUNCHER = '/home/hero/minecraft/launch.sh'
BLACKLIST_PATH = J(WORKING_DIR, "blacklist.txt")

END_OF_STREAM = 'end_of_stream.txt'
ACTION_FILE = "actions.tmcpr"
BAD_MARKER_NAME, GOOD_MARKER_NAME = 'INVALID', 'VALID'
SKIPPED_RENDER_FLAG = 'SKIPPED_RENDER'

METADATA_FILES = [
    'metaData.json',
    'markers.json',
    'mods.json',
    'stream_meta_data.json']

VIDEO_FILES = [
    'metaData.json',
    'markers.json',
    'mods.json',
    'stream_meta_data.json']


# Takes in a Video_dir and a Json_dir and puts the results in Combined_dir
def copy_skips(target_dir, source_dir):
    assert target_dir != source_dir

    print('Collecting files to copy')
    copy_ops = []

    for path in os.walk(target_dir):
        to_copy = []

        # Find skip file
        src = J(source_dir, path, BAD_MARKER_NAME)
        dst = J(target_dir, path, BAD_MARKER_NAME)
        print(src)
        if E(src):
            to_copy.append((src, dst))
        else:
            continue

        copy_ops.append(to_copy)

    for copy in tqdm(copy_ops):
        for src, dest in tqdm(copy):
            shutil.copyfile(src, dest)


