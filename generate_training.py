from fractions import Fraction
from collections import OrderedDict
import skvideo.io
import pickle
import numpy
import json
import tqdm
import os

J = os.path.join
E = os.path.exists
WORKING_DIR = "output"
DATA_DIR = J(WORKING_DIR, "merged")
RENDER_DIR = J(WORKING_DIR, "rendered")
BLACKLIST_PATH =J(WORKING_DIR, "blacklist.txt")

END_OF_STREAM = 'end_of_stream.txt'
ACTION_FILE = "actions.tmcpr"
END_OF_STREAM_TEXT = 'This is the end.'
BAD_MARKER_NAME, GOOD_MARKER_NAME = 'INVALID', 'VALID'


def genSarsaPairs(inputPath, recordingName, outputPath):
    # Script to to pair actions with video recording
    # All times are in ms and we assume a actions list, a timestamp file, and a dis-syncronous mp4 video

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
    for marker in json.load(open(J(inputPath,'./markers.json'))):
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

    # Frames per second expressed as a fraction, e.g. 25/1
    fps = float(sum(Fraction(s) for s in metadata['video']['@r_frame_rate'].split()))
    timePerFrame = 1000.0 / fps
    videoOffset = 5000
    numFrames = metadata['video']['@nb_frames']


    actionTime = iter(zip(timestamps, actions))
    currentTime  = 0
    desieredTimestamp = 0 # Timestamps index
    currentFrame = 0     # videogen index
    frame = None
    action = None

    print("Video has", numFrames, "frames at", fps, "fps")
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
        videogen = skvideo.io.vreader("./recording.mp4", inputdict=params)

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
                except StopIteration:
                    # Be lazy
                    print("ERROR PARSING VIDEO")
                    print("Could not get enough frames to fill timestamp file")
                    print(currentTime)
                    print(desieredTimestamp)
                    print(roundToFrame(currentTime))
                    print(roundToFrame(desieredTimestamp))
                    exit(-1)

            # Generate numpy pair and append 

            try:
                sarsa = (next(videogen), action)
                currentTime += timePerFrame
                pbar2.update(1)
                sarsa_pairs.append(sarsa)
            except StopIteration:
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
        if not os.path.exists(J(outPath, experementName)):
            os.makedirs(J(outPath, experementName))
        numpy.save(J(outPath, experementName, str(startTime) + '-' + str(stopTime), '.npy'), sarsa_pairs)

    

    

        
