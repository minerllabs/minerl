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
    split_cmd = ['ffmpeg', '-i', J(inputPath, 'recording.mp4'),
                 '-c:a', 'copy',
                 '-c:v', 'copy',
                 '-force_key_frames',
                 ','.join(keyframes), J(inputPath, 'keyframes_recording.mp4')]
    # print('Running: ' + ' '.join(split_cmd))

    try:
        subprocess.check_output(split_cmd, stderr=subprocess.STDOUT)
    except Exception as e:
        print('COMMAND FAILED:', e)
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


def parse_metadata(startMarker, endMarker):
    try:
        metadata = {}
        startMeta = startMarker['value']['metadata']
        endMeta = endMarker['value']['metadata']
        metadata['start_position'] = startMarker['value']['position']
        metadata['end_position'] = endMarker['value']['position']
        metadata['start_tick'] = startMeta['tick'] if 'tick' in startMeta else None
        metadata['end_tick'] = endMeta['tick'] if 'tick' in endMeta else None
        metadata['start_time'] = startMarker['realTimestamp']
        metadata['end_time'] = endMarker['realTimestamp']

        # Recording the string sent to us by Minecraft server including experiment specific data like if we won or not
        metadata['server_info_str'] = endMeta['expMetadata']
        metadata['server_metadata'] = json.loads(endMeta['expMetadata'][endMeta['expMetadata'].find('experimentMetadata') + 19:-1])

        # Not meaningful in some older streams but included for completeness
        metadata['server_info_str_start'] = startMeta['expMetadata']
        metadata['server_metadata_start'] = json.loads(startMeta['expMetadata'][startMeta['expMetadata'].find('experimentMetadata') + 19:-1])

        return metadata
    except ValueError:
        return {'BIG_FAT_ERROR': True}

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


def _gen_sarsa_pairs(outputPath, manager, input):
    n = manager.get_index()
    recordingName, inputPath = input
    ret = gen_sarsa_pairs(outputPath, inputPath, recordingName, lineNum=n)
    manager.free_index(n)
    return ret


# 3. generate sarsa pairs
def gen_sarsa_pairs(outputPath, inputPath, recordingName, lineNum=None):
    # Script to to pair actions with video recording
    # All times are in ms and we assume a actions list, a timestamp file, and a dis-syncronous mp4 video

    # Decide if absolute or relative (old format)
    # Disable data generation for old format
    if E(J(inputPath, 'metaData.json')):
        metadata = json.load(open(J(inputPath, 'metaData.json')))
        if 'generator' in metadata:
            version = metadata['generator'].split('-')[-2]
            if int(version) < 103:
                return 0
    else:
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

    # for key, marker in sorted(markers.items()):
    #     malformedStr = marker['value']['metadata']['expMetadata']
    #     jsonThing = json.loads(malformedStr[malformedStr.find('experimentMetadata') + 19:-1])
    #     expName = ''
    #     if 'experiment_name' in jsonThing:
    #         expName = jsonThing['experiment_name']
    #     startTime = streamMetadata['start_timestamp']
    #     approxTime = (key - startTime) / 60000
    #     startRecording = marker['value']['metadata']['startRecording']
    #     stopRecording = marker['value']['metadata']['stopRecording']
    #     #print('key: {}, approx time: {} minutes and {} seconds, experiment name: {}, start: {}, stop: {}'.format(key, int(approxTime), 60 * (approxTime - int(approxTime)), expName, startRecording, stopRecording))

    startTime = None
    startTick = None
    startMarker = None
    experimentName = ""
    # print(sorted(markers.items()))
    for key, marker in sorted(markers.items()):
        expName = ""
        # Get experiment name (its a malformed json so we have to look it up by hand)
        if 'value' in marker and 'metadata' in marker['value'] and 'expMetadata' in marker['value']['metadata']:
            meta = marker['value']['metadata']

            malformedStr = meta['expMetadata']
            jsonThing = json.loads(malformedStr[malformedStr.find('experimentMetadata') + 19:-1])
            if 'experiment_name' in jsonThing:
                expName = jsonThing['experiment_name']
            else:
                continue 

        if 'startRecording' in meta and meta['startRecording'] and 'tick' in meta:
            # If we encounter a start marker after a start marker there is an error and we should throw away this segemnt
            startTime = key
            startTick = meta['tick']
            startMarker = marker

        if 'stopRecording' in meta and meta['stopRecording'] and startTime != None:
            segments.append((startTick, startMarker, meta['tick'], marker, expName))
            startTime = None
            startTick = None

    #print(segments)
    # Layout of segments
    # 0.           1.             2.          3.            4.
    # Start Tick : Start Marker : Stop Tick : Stop Marker : Experiment Name

    if not E(J(inputPath, "recording.mp4")):
        return 0

    if len(markers) == 0:
        return 0

    segments = [segment for segment in segments if segment[2] - segment[0] > EXP_MIN_LEN_TICKS and segment[0] > 0]

    if not segments:
        return 0
    try:
        if not E(J(inputPath, 'keyframes_recording.mp4')):
            # os.remove(J(inputPath, 'keyframes_recording.mp4'))
            add_key_frames(inputPath, segments)
    except subprocess.CalledProcessError as exception:
        print("Error splitting {}:\033[0;31;47m {}        \033[0m 0;31;47m".format(recordingName, exception))
        return 0 

    json_data = open(J(inputPath, 'univ.json')).read()
    univ_json = json.loads(json_data)

    for pair in tqdm.tqdm(segments, desc='Segments', leave=False, position=lineNum):
        time.sleep(0.05)
        startTick = pair[0]
        stopTick = pair[2]
        startTime = startTick / 20.0
        stopTime = stopTick / 20.0
        experimentName = pair[-1]

        experiment_id = recordingName + "_" + str(int(startTime * 50)) + '-' + str(int(stopTime * 50))
        output_name = J(outputPath, experimentName, experiment_id, 'recording.mp4')
        univ_output_name = J(outputPath, experimentName, experiment_id, 'univ.json')
        meta_output_name = J(outputPath, experimentName, experiment_id, 'metadata.json')
        output_dir = os.path.dirname(output_name)
        if not E(output_dir):
            os.makedirs(output_dir)
        if not (E(output_name) and E(univ_output_name) and E(meta_output_name)):
            try:
                # Remove potentially stale elements
                if E(output_name): os.remove(output_name)
                if E(univ_output_name): os.remove(univ_output_name)
                if E(meta_output_name): os.remove(meta_output_name)

                # Split video (without re-encoding)
                extract_subclip(inputPath, startTime, stopTime, output_name)

                # Split universal action json
                json_to_write = {}
                for idx in range(startTick, stopTick + 1):
                    json_to_write[str(idx - startTick)] = univ_json[str(idx)]
                json.dump(json_to_write, open(univ_output_name, 'w'))

                # Split metadata.json
                metadata = parse_metadata(pair[1], pair[3])
                json.dump(metadata, open(meta_output_name, 'w'))

                numNewSegments += 1

            except KeyboardInterrupt:
                return numNewSegments
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
    numSegments = []

    try:
        numW = 8
        multiprocessing.freeze_support()
        with multiprocessing.Pool(numW, initializer=tqdm.tqdm.set_lock, initargs=(multiprocessing.RLock(),)) as pool:
            manager = ThreadManager(multiprocessing.Manager(), numW, 1, 1)
            func = functools.partial(_gen_sarsa_pairs, DATA_DIR, manager)
            numSegments = list(tqdm.tqdm(pool.imap_unordered(func, valid_renders), total=len(valid_renders), desc='Files', miniters=1, position=0, maxinterval=1))

            # for recording_name, render_path in tqdm.tqdm(valid_renders, desc='Files'):
            #     numSegmentsRendered += gen_sarsa_pairs(render_path, recording_name, DATA_DIR)
    except Exception as e:
        print('\n' * numW)
        print(e)
        print('Rendered {} new segments in total!'.format(sum(numSegments)))
        print('LIST OF FAILED COMMANDS:')
        print(FAILED_COMMANDS)
        return

    numSegmentsRendered = sum(numSegments)

    print('\n' * numW)
    print('Rendered {} new segments in total!'.format(numSegmentsRendered))
    print('LIST OF FAILED COMMANDS:')
    print(FAILED_COMMANDS)

if __name__ == "__main__":
    main()

