import os
import sys

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


# Takes in a Video_dir and a Json_dir and puts the results in Combined_dir
def merge_dirs(video_dir, json_dir, out_dir, copyMetaFiles=True):
    assert video_dir != json_dir != out_dir

    print('Collecting files to copy')
    copy_ops = []

    for path in os.listdir(json_dir):
        to_copy = []

        # Make sure dir is valid
        if E(J(json_dir, path, GOOD_MARKER_NAME)) and E(J(video_dir, path, GOOD_MARKER_NAME)):
            to_copy.append((J(json_dir, path, GOOD_MARKER_NAME), J(out_dir, path, GOOD_MARKER_NAME)))
        else:
            print('File not valid in both src folders')
            continue

        # Find universal file
        univ = J(json_dir, path, 'univ.json')
        dst  = J(out_dir, path, 'univ.json')
        if E(univ):
            to_copy.append((univ, dst))
        else:
            continue

        # Find metadata files
        if copyMetaFiles:
            missingMeta = False
            for file in METADATA_FILES:
                fpath = J(json_dir, path, file)
                fdst  = J(out_dir, path, file)
                if E(fpath):
                    to_copy.append((fpath, fdst))
                else:
                    missingMeta = True
            if missingMeta:
                continue

        # Find video files
        recording = J(video_dir, path, 'recording.mp4')
        rec_dst   = J(out_dir, path, 'recording.mp4')
        if E(recording):
            to_copy.append((recording, rec_dst))
            # keyframes = J(video_dir, path, 'keyframes_recording.mp4')
            # key_dest  = J(out_dir, path, 'keyframes_recording.mp4')
            # # Keyframes are optional but speed up subsequent generate calls
            # if E(keyframes):
            #     to_copy.append((keyframes, key_dest))
        else:
            continue

        copy_ops.append(to_copy)

    for copy in tqdm(copy_ops):
        for src, dest in tqdm(copy):
            if not E(dest):
                if not E(os.path.dirname(dest)):
                    try:
                        os.makedirs(os.path.dirname(dest))
                    except OSError as exc:  # Guard against race condition
                        print(exc)
                shutil.copyfile(src, dest)

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        print('Take videos from', sys.argv[1])
        print('Take jsons from', sys.argv[2])
        print('Put result in', sys.argv[3])
        if len(sys.argv) == 5:
            cont = sys.argv[4]
        else:
            cont = input('Type yes to continue: ')

        if cont == 'yes' or cont == 'y':
            merge_dirs(sys.argv[1], sys.argv[2], sys.argv[3])
        else:
            print('Quiting')
