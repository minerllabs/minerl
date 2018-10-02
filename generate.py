"""
render.py  
# This script renders the merged experiments into 
# actions and videos by doing the following
# 1) Unzipping various mcprs and building render directories 
#    containing meta data.
# 2) Running the action_rendering scripts
# 3) Running the video_rendering scripts
"""
from fractions import Fraction
from collections import OrderedDict
import os
import numpy
import tqdm
import zipfile
import subprocess
import json
import moviepy
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

#######################
### UTILITIES
#######################
J = os.path.join
E = os.path.exists
EXP_MIN_LEN = 20
WORKING_DIR = os.path.abspath("./output")
DATA_DIR = J(WORKING_DIR, "data")

RENDER_DIR = J(WORKING_DIR, "rendered")
BLACKLIST_PATH = J(WORKING_DIR, "blacklist.txt")

ACTION_FILE = "actions.tmcpr"
BAD_MARKER_NAME, GOOD_MARKER_NAME = 'INVALID', 'VALID'

METADATA_FILES = [
    'metaData.json',
    'markers.json',
    'mods.json',
    'stream_meta_data.json']


def touch(path):
    with open(path, 'w'):
        pass


def remove(path):
    if E(path):
        os.remove(path)


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
    if not E(RENDER_DIR):
        os.makedirs(RENDER_DIR)

    render_dirs = []
    for filename in tqdm.tqdm(next(os.walk(RENDER_DIR))[1]):
        render_path = J(RENDER_DIR, filename)

        if not E(render_path):
            continue

        render_dirs.append((filename, render_path))

    return render_dirs


# 2. get metadata from the files.
def get_metadata(renders: list) -> list:
    """
	Unpacks the metadata of a recording and checks its validity.
	"""
    good_renders = []
    bad_renders = []

    for recording_name, render_path in tqdm.tqdm(renders):
        if E(render_path):
            # Check if metadata has already been extracted.
            # If it has been computed see if it is valid
            # or not.
            if E(J(render_path, GOOD_MARKER_NAME)):
                good_renders.append((recording_name, render_path))
            else:
                bad_renders.append((recording_name, render_path))

    return good_renders, bad_renders


# 3. generate sarsa pairs
def gen_sarsa_pairs(inputPath, recordingName, outputPath):
    # Script to to pair actions with video recording
    # All times are in ms and we assume a actions list, a timestamp file, and a dis-syncronous mp4 video

    # Decide if absolute or relative
    isAbsolute = False
    if E(J(inputPath, 'metaData.json')):
        metadata = json.load(open(J(inputPath, 'metaData.json')))
        if 'generator' in metadata:
            version = metadata['generator'].split('-')[-2]
            if int(version) < 103:
                isAbsolute = True
    else:
        return

    # Disable data generation for old format
    if isAbsolute:
        return

    # Generate recording segments
    # Sorted pairs of (start, stop, exprementName) timestamps (in ms)
    segments = []

    markers = OrderedDict()
    for marker in json.load(open(J(inputPath, 'markers.json'))):
        markers[marker['realTimestamp']] = marker

    startTime = None
    experementName = ""
    for key, marker in sorted(markers.items()):
        expName = ""
        # Get experement name (its a malformed json so we have to look it up by hand)
        if 'value' in marker and 'metadata' in marker['value'] and 'expMetadata' in marker['value']['metadata']:
            marker = marker['value']['metadata']

            malformedStr = marker['expMetadata']
            jsonThing = json.loads(malformedStr[malformedStr.find('experimentMetadata') + 19:-1])
            if 'experiment_name' in jsonThing:
                expName = jsonThing['experiment_name']
            else:
                continue

        if 'startRecording' in marker and marker['startRecording']:
            # If we encounter a start marker after a start marker there is an error and we should throw away this segemnt
            startTime = key
            experementName = expName

        if 'stopRecording' in marker and marker['stopRecording'] and startTime != None:
            # Experement name should be the same
            if experementName == expName:
                segments.append((startTime, key, expName))
            startTime = None

    if not E(J(inputPath, "recording.mp4")):
        return

    if len(markers) == 0:
        return

    streamMetadata = json.load(open(J(inputPath, 'stream_meta_data.json')))

    # Frames per second expressed as a fraction, e.g. 25/1
    fps = 20  # float(sum(Fraction(s) for s in metadata['video']['@r_frame_rate'].split()))
    videoOffset = streamMetadata['start_timestamp']
    numFrames = streamMetadata['stop_timestamp'] - videoOffset

    for pair in (segments):

        startTime = (pair[0])/1000.0
        stopTime = (pair[1])/1000.0
        if stopTime - startTime <= EXP_MIN_LEN:
            continue
        experementName = pair[2]

        output_name = J(outputPath, experementName, recordingName + "_" + str(startTime) + '-' + str(stopTime) + '.mp4')
        output_dir = os.path.dirname(output_name)
        if not E(output_dir):
            os.makedirs(output_dir)
        tqdm.tqdm.write(output_name)
        ffmpeg_extract_subclip(J(inputPath, "recording.mp4"), startTime, stopTime,
                               targetname=output_name)


def main():
    """
    The main render script.
    """
    # 1. Load the blacklist.
    blacklist = set(numpy.loadtxt(BLACKLIST_PATH, dtype=numpy.str).tolist())

    print("Constructing data directory.")
    renders = construct_data_dirs(blacklist)

    print("Retrieving metadata from files:")
    valid_renders, invalid_renders = get_metadata(renders)
    print(len(valid_renders))
    print("... found {} valid recordings and {} invalid recordings"
          " out of {} total files".format(
        len(valid_renders), len(invalid_renders), len(os.listdir(RENDER_DIR)))
    )
    print("Rendering videos: ")
    for recording_name, render_path in tqdm.tqdm(valid_renders):
        gen_sarsa_pairs(render_path, recording_name, DATA_DIR)


if __name__ == "__main__":
    main()
