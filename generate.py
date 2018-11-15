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
import time
import numpy
import tqdm
import zipfile
import subprocess
import json

#######################
### UTILITIES
#######################
J = os.path.join
E = os.path.exists
EXP_MIN_LEN_TICKS = 20 * 30 # 30 sec
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


def format_seconds(seconds):
    """
    Given seconds (int) returns a string of format hour:minutes:seconds
    """
    hours = int(seconds / 3600)
    seconds = seconds - hours * 3600
    minutes = int(seconds / 60)
    seconds = seconds - minutes * 60
    seconds = round(seconds, 3)
    return str(hours) + ':' + str(minutes) + ':' + str(seconds)


def add_key_frames(inputPath, segments):
    keyframes = []
    for segment in segments:
        keyframes.append(format_seconds(segment[0]))
        keyframes.append(format_seconds(segment[1]))
    split_cmd = ['ffmpeg', '-i', J(inputPath, 'recording.mp4'), '-force_key_frames',
                 ','.join(keyframes), J(inputPath, 'keyframes_recording.mp4')]
    #print('Running: ' + ' '.join(split_cmd))

    try:
        subprocess.check_output(split_cmd, stderr=subprocess.STDOUT)
    except:
        print('COMMAND FAILED:')
        print(split_cmd)
        FAILED_COMMANDS.append(split_cmd)


def extract_subclip(inputPath, start_time, stop_time, output_name):
    split_cmd = ['ffmpeg', '-ss', format_seconds(start_time), '-i',
                 J(inputPath, 'keyframes_recording.mp4'), '-t', format_seconds(stop_time - start_time),
                 '-vcodec', 'copy', '-acodec', 'copy', '-y', output_name]
    #print('Running: ' + ' '.join(split_cmd))
    try:
        subprocess.check_output(split_cmd, stderr=subprocess.STDOUT)
    except:
        print('COMMAND FAILED:')
        print(split_cmd)
        FAILED_COMMANDS.append(split_cmd)


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
        return 0

    # Disable data generation for old format
    if isAbsolute:
        return 0

    # Generate recording segments
    # Sorted pairs of (start, stop, exprementName) timestamps (in ms)
    segments = []
    numNewSegments = 0

    markers = OrderedDict()
    streamMetadata = json.load(open(J(inputPath, 'stream_meta_data.json')))

    if 'markers' in streamMetadata:
        markers_sp = streamMetadata['markers']
        for marker in markers_sp:
            markers[marker['realTimestamp']] = marker
            # if 'metadata' in marker['value']:
            #     if 'tick' in marker['value']['metadata']:
            #         markers[marker['value']['metadata']['tick']] = marker
            #     else:
            #         print("{} has missing tick!".format(recordingName))

    for key, marker in sorted(markers.items()):
        malformedStr = marker['value']['metadata']['expMetadata']
        jsonThing = json.loads(malformedStr[malformedStr.find('experimentMetadata') + 19:-1])
        expName = ''
        if 'experiment_name' in jsonThing:
            expName = jsonThing['experiment_name']
        startTime = streamMetadata['start_timestamp']
        approxTime = (key - startTime) / 60000
        startRecording = marker['value']['metadata']['startRecording']
        stopRecording = marker['value']['metadata']['stopRecording']
        #print('key: {}, approx time: {} minutes and {} seconds, experiment name: {}, start: {}, stop: {}'.format(key, int(approxTime), 60 * (approxTime - int(approxTime)), expName, startRecording, stopRecording))

    startTime = None
    startTick = None
    experimentName = ""
    for key, marker in sorted(markers.items()):
        expName = ""
        # Get experiment name (its a malformed json so we have to look it up by hand)
        if 'value' in marker and 'metadata' in marker['value'] and 'expMetadata' in marker['value']['metadata']:
            marker = marker['value']['metadata']

            malformedStr = marker['expMetadata']
            jsonThing = json.loads(malformedStr[malformedStr.find('experimentMetadata') + 19:-1])
            if 'experiment_name' in jsonThing:
                expName = jsonThing['experiment_name']
            else:
                continue 

        if 'startRecording' in marker and marker['startRecording'] and 'tick' in marker:
            # If we encounter a start marker after a start marker there is an error and we should throw away this segemnt
            startTime = key
            #experimentName = expName
            startTick = marker['tick']

        if 'stopRecording' in marker and marker['stopRecording'] and startTime != None:
            # experiment name should be the same
            # if experimentName == expName:
            segments.append((startTime, key, expName, startTick, marker['tick']))
            startTime = None
            startTick = None

    #print(segments)

    if not E(J(inputPath, "recording.mp4")):
        return 0

    if len(markers) == 0:
        return 0

    # Frames per second expressed as a fraction, e.g. 25/1
    fps = 20  # float(sum(Fraction(s) for s in metadata['video']['@r_frame_rate'].split()))
    videoOffset_ms = streamMetadata['start_timestamp']
    #print("offset: {}".format(videoOffset_ms))
    length_ms = streamMetadata['stop_timestamp'] - videoOffset_ms

    # TODO remove in favor of an exact calculation
    videoOffset_ticks = -1#-int(videoOffset_ms / 50)

    segments = [((segment[0] - videoOffset_ms) / 1000, (segment[1] - videoOffset_ms) / 1000, segment[2], segment[3] - videoOffset_ticks, segment[4] - videoOffset_ticks) for segment in segments]
    segments = [segment for segment in segments if segment[4] - segment[3] > EXP_MIN_LEN_TICKS and segment[3] > 0]
    if not segments:
        return 0
    if not E(J(inputPath, 'keyframes_recording.mp4')):
        add_key_frames(inputPath, segments)

    json_data = open(J(inputPath, 'univ.json')).read()
    univ_json = json.loads(json_data)

    for pair in tqdm.tqdm(segments, desc='Segments', leave=False):
        time.sleep(0.1)
        startTime = pair[0]
        startTime = pair[3] / 20.0
        stopTime = pair[1]
        stopTime = pair[4] / 20.0
        experimentName = pair[2]
        #print('Starttime: {}'.format(format_seconds(startTime)))
        #print('Stoptime: {}'.format(format_seconds(stopTime)))
        #print('Number of seconds: {}'.format(stopTime - startTime))
        #print('Start tick: {}'.format(pair[3]))
        #print('Stop tick: {}'.format(pair[4]))
        #print('Number of ticks: {}'.format(pair[4] - pair[3] + 1))
        json_ticks = [int(key) for key in univ_json.keys()]
        #print('min tick: {} max tick: {}'.format(min(json_ticks), max(json_ticks)))

        experiment_id = recordingName + "_" + str(int(startTime * 50)) + '-' + str(int(stopTime * 50))
        output_name = J(outputPath, experimentName, experiment_id, 'recording.mp4')
        output_dir = os.path.dirname(output_name)
        if not E(output_dir):
            os.makedirs(output_dir)
        tqdm.tqdm.write(output_name)
        if not E(output_name):
            numNewSegments += 1
            extract_subclip(inputPath, startTime, stopTime, output_name)
            univ_output_name = J(outputPath, experimentName, experiment_id, 'univ.json')
            json_to_write = {}
            try:
                for idx in range(pair[3], pair[4] + 1):
                    json_to_write[str(idx - pair[3])] = univ_json[str(idx)]
                json.dump(json_to_write, open(univ_output_name, 'w'))
            except Exception as e:
                print(e)
                continue
    return numNewSegments

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
    numSegmentsRendered = 0
    for recording_name, render_path in tqdm.tqdm(valid_renders, desc='Files'):
        numSegmentsRendered += gen_sarsa_pairs(render_path, recording_name, DATA_DIR)

    print('Rendered {} new segments in total!'.format(numSegmentsRendered))
    print('LIST OF FAILED COMMANDS:')
    print(FAILED_COMMANDS)

if __name__ == "__main__":
    main()
