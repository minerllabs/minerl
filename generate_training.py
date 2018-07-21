import skvideo
import pickle
import numpy

# Script to to pair actions with video recording
# All times are in ms and we assume a actions list, a timestamp file, and a dis-syncronous mp4 video


# Load actions
actions, timestamps = pickle.load(open("./actions.pkl", 'wb'))

# Load video
videogen = skvideo.io.vreader("./recording.mp4")
metadata = skvideo.io.ffprobe("./recording.mp4")

# Create index of video frame counts
 
 # This gets messy really fast - how do we know that a frame is generated from the begining of the file (it's not it plays a second of data first)
 # how do we know that it really renders at 60hz? (or framerate) well we hope that it will

fps = 60
timePerFrame = 1000 / 60
videoOffset = 1000
numFrames = metadata['video']['nb_frames']

currentFrameId = 0
currentFrame = None
action = None

sarsa_pairs = []

for time in timestamps:
    frameNum = int(round((time - 1000) / timePerFrame))
    try:
        action = next(actions)
    except StopIteration:
        break

    # Get the frame in quesiton
    while (frameNum > currentFrame) :
        try:
            currentFrame = next(videogen)
            currentFrame += 1
        except StopIteration:
            # Be lazy
            exit(-1)

    # Generate numpy pair and append 
    if (currentFrame != None and action != None)
        sarsa = (currentFrame, action)
        sarsa_pairs.append(sarsa)

outFile = open('data.npy', 'w+')
numpy.save(outFile, sarsa_pairs)

    

    

        
