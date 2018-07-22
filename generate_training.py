from fractions import Fraction
from collections import OrderedDict
import skvideo.io
import pickle
import numpy
import json
import tqdm
import os

# Script to to pair actions with video recording
# All times are in ms and we assume a actions list, a timestamp file, and a dis-syncronous mp4 video

filename = 'corrupt_bread_deamon'

# Load actions
#actions, timestamps = pickle.load(open("./actions.pkl", 'wb'))
actions = numpy.load('./network.npy')
timestamps = numpy.load('./timestamp.npy')

# Load video
#videogen = skvideo.io.vreader("./recording.mp4")
metadata = skvideo.io.ffprobe("./recording.mp4")

# Generate recording segments
# Sorted pairs of (start, stop, exprementName) timestamps (in ms)
segments = []

markers = OrderedDict()
for marker in json.load(open('./markers.json')):
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


# Frames per second expressed as a fraction, e.g. 25/1
fps = float(sum(Fraction(s) for s in metadata['video']['@r_frame_rate'].split()))
timePerFrame = 1000.0 / fps
videoOffset = 6000
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
    while (currentTime <= stopTime):
        frame = None
        # Get the closest frame
        while (roundToFrame(currentTime) < roundToFrame(desieredTimestamp)) :
            try:
                next(videogen)
                currentTime += timePerFrame
                pbar2.update(1)
                print("", end="")
            except StopIteration:
                # Be lazy
                print("ERROR PARSING VIDEO")
                print("Could not get enough frames to fill timestamp file")
                exit(-1)

        # Generate numpy pair and append 
        sarsa = (next(videogen), action)
        currentTime += timePerFrame
        pbar2.update(1)
        sarsa_pairs.append(sarsa)

        # Itterate action and timestamp
        try:
            (desieredTimestamp, action) = next(actionTime)
            pbar.update(1)
            print("", end="")
        except StopIteration:
            break

    if( not os.path.exists('data/')):
        os.makedirs('data/')
    if not os.path.exists('data/{}/'.format(experementName)):
        os.makedirs('data/{}/'.format(experementName))
    numpy.save('data/{}/{}.npy'.format(experementName,filename + str(startTime) + '-' + str(stopTime)), sarsa_pairs)

    

    

        
