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
import skvideo.io
import os
import numpy 
import tqdm
import zipfile
import subprocess
import json

######################3
### UTILITIES
#######################
J = os.path.join
E = os.path.exists
WORKING_DIR = os.path.abspath("./output")
DATA_DIR = J(WORKING_DIR, "data")

RENDER_DIR = J(WORKING_DIR, "rendered")
BLACKLIST_PATH =J(WORKING_DIR, "blacklist.txt")

END_OF_STREAM = 'end_of_stream.txt'
ACTION_FILE = "actions.tmcpr"
END_OF_STREAM_TEXT = 'This is the end.'
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
			if E(J(render_path, END_OF_STREAM)):
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

    #Decide if absolute or relative
    isAbsolute = False
    if E(J(inputPath,'metaData.json')):
        metadata = json.load(open(J(inputPath,'metaData.json')))
        if 'generator' in metadata:
            version = metadata['generator'].split('-')[-2]
            print("SHIIIIIIITTTT:", version)
            if int(version) < 103:
                isAbsolute = True
    else:
        return

    # Load actions
    #actions, timestamps = pickle.load(open("./actions.pkl", 'wb'))
    actions = numpy.load(J(inputPath, 'network.npy'))
    timestamps = numpy.load(J(inputPath, 'timestamp.npy'))

    # Load video
    #videogen = skvideo.io.vreader("./recording.mp4")

    # Test if folder has video
    metadata = None
    if E(J(inputPath,'recording.mp4')):
        metadata = skvideo.io.ffprobe(J(inputPath,'recording.mp4'))
    if metadata is None:
        return

    # Generate recording segments
    # Sorted pairs of (start, stop, exprementName) timestamps (in ms)
    segments = []

    markers = OrderedDict()
    for marker in json.load(open(J(inputPath,'markers.json'))):
        markers[marker['realTimestamp']] = marker

    startTime = None
    experementName = ""
    for key, marker in sorted(markers.items()):
        expName = ""
        # Get experement name (its a malformed json so we have to look it up by hand)
        if 'value' in marker and 'metadata' in marker['value'] and 'expMetadata' in marker['value']['metadata']:
            marker = marker['value']['metadata']
            malformedStr = marker['expMetadata']
            jsonThing = json.loads(malformedStr[malformedStr.find('experimentMetadata')+19:-1])
            if 'experiment_name' in jsonThing:
                expName = jsonThing['experiment_name']
            else:
                continue

        if 'startRecording' in marker and marker['startRecording']:
            # If we encounter a start marker after a start marker there is an error and we should throw away this segemnt
            startTime = key
            experementName = expName
        
        if 'stopRecording' in marker and marker['stopRecording'] and startTime != None:
            #Experement name should be the same
            if experementName == expName:
                segments.append((startTime, key, expName))
            startTime = None

    if len(markers) == 0:
        return

    # if 'video' not in metadata:
    #     return
    # Frames per second expressed as a fraction, e.g. 25/1
    fps = 60 # float(sum(Fraction(s) for s in metadata['video']['@r_frame_rate'].split()))
    timePerFrame = 1000.0 / fps
    videoOffset = 5000
    # numFrames = metadata['video']['@nb_frames']


    actionTime = iter(zip(timestamps, actions))
    currentTime  = 0
    desieredTimestamp = 0 # Timestamps index
    currentFrame = 0     # videogen index
    frame = None
    action = None

    print("Video has", 1, "frames at", fps, "fps")
    def roundToFrame(x):
        return round(x/timePerFrame)*timePerFrame

    print(segments)
    for line in segments:
        print(line)

    pbar = tqdm.tqdm(total=len(actions))
    pbar2 = tqdm.tqdm()

    for pair in segments:
        print()
        print("Segment:", pair[0], "-", pair[1], pair[2])
        sarsa_pairs = []
        startTime = pair[0]
        stopTime = pair[1]
        experementName = pair[2]

        if (stopTime - startTime > 1000000):
            print('skipping massive shard')
            continue

        # Move timestamp file to start time
        while (desieredTimestamp < startTime):
            try:
                (desieredTimestamp, action) = next(actionTime)
                pbar.update(1)
                print("", end="")
            except StopIteration:
                # Be lazy
                print("ERROR")
                print("Could not get enough timestamp action pairs")
                exit(-1)

        #frameNum = int(round((startTime - videoOffset) / timePerFrame))

        currentTime = roundToFrame(startTime - videoOffset - 2000)
        
        # currentFrame = int(frameSec * fps)
        params = {"-ss":str(currentTime/1000)}
        videogen = skvideo.io.vreader(J(inputPath,'recording.mp4'), inputdict=params)

        # Record the aciton pair 
        while (currentTime <= stopTime - videoOffset):
            frame = None
            # Get the closest frame
            while (roundToFrame(currentTime) < roundToFrame(desieredTimestamp - videoOffset)) :
                try:
                    next(videogen)
                    currentTime += timePerFrame
                    pbar2.update(1)
                    print("", end="")
                except:
                    # Be lazy
                    print("ENDING VIDEO")
                    print("Could not get enough frames to fill timestamp file")
                    print(currentTime)
                    print(desieredTimestamp)
                    print(roundToFrame(currentTime))
                    print(roundToFrame(desieredTimestamp))
                    break

            # Generate numpy pair and append 

            try:
                sarsa = (next(videogen), action)
                currentTime += timePerFrame
                pbar2.update(1)
                sarsa_pairs.append(sarsa)
            except:
                print(currentTime)
                print(desieredTimestamp)
                print(roundToFrame(currentTime))
                print(roundToFrame(desieredTimestamp))
                break


            # Itterate action and timestamp
            try:
                (desieredTimestamp, action) = next(actionTime)
                pbar.update(1)
                print("", end="")
            except StopIteration:
                break

        if( not os.path.exists(outputPath)):
            os.makedirs(outputPath)
        if not os.path.exists(J(outputPath, experementName)):
            os.makedirs(J(outputPath, experementName))
        if isAbsolute:
            numpy.save(J(outputPath, experementName, recordingName + str(startTime) + '-' + str(stopTime) + '_ABS_.npy'), sarsa_pairs)
        else:
            numpy.save(J(outputPath, experementName, recordingName + str(startTime) + '-' + str(stopTime) + '.npy'), sarsa_pairs)


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