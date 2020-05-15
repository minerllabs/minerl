import os

J =  os.path.join
E = os.path.exists

BASE_DIR = os.environ.get('MINERL_OUTPUT_ROOT', os.path.expanduser(
    J('~', 'minerl_data')
) )

RENDERERS_DIR = os.path.expanduser(
    J('~', 'renderers'))
NUM_MINECRAFTS=20


OUTPUT_DIR = J(BASE_DIR, 'output')
DOWNLOAD_DIR = J(BASE_DIR, 'downloaded_sync')
BUCKET_NAME = 'pizza-party'

# MERGING
MERGED_DIR = J(OUTPUT_DIR, 'merged')
BLACKLIST_TXT = J(OUTPUT_DIR, 'blacklist.txt')
PARSE_COMMAND = [os.path.abspath(J('merging', 'parse')), '-f']
Z7_COMMAND = ["7z"]
TEMP_ROOT='/tmp'
BLOCK_SIZE = 1024*1024
ACTION_FILE = 'actions.tmcpr'
RECORDING_FILE = 'recording.tmcpr'
TEMP_FILE = 'tmp.tmcpr'
GLOB_STR_BASE = J(DOWNLOAD_DIR, "*", "*", "*", "*")


#### RENDERING

RENDER_DIR = J(OUTPUT_DIR, "rendered")
MINECRAFT_DIR = [J(RENDERERS_DIR, 'minecraft_{}'.format(i)) for i in range(NUM_MINECRAFTS)]
RECORDING_PATH = [J(d, 'replay_recordings') for d in MINECRAFT_DIR]
RENDERED_VIDEO_PATH = [J(d, 'replay_videos') for d in MINECRAFT_DIR]
RENDERED_LOG_PATH = [J(d,  'replay_logs') for d in MINECRAFT_DIR]
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