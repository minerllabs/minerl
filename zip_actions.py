#!/usr/bin/python3.5
"""
render.py
# This script renders the merged experiments into
# actions and videos by doing the following
# 1) Unzipping various mcprs and building render directories
#    containing meta data.
# 2) Running the action_rendering scripts
# 3) Running the video_rendering scripts
"""
import argparse
import glob
import json
import os
import re
import struct
import subprocess
import time
from multiprocessing import Pool
from shutil import copyfile

import numpy as np
import tqdm

# UTILITIES
#######################
J = os.path.join
E = os.path.exists


ACTION_FILE = 'actions.tmcpr'
RECORDING_FILE = 'recording.tmcpr'
TEMP_FILE = 'tmp.tmcpr'

def touch(path):
    with open(path, 'w'):
        pass

def remove(path):
    if E(path):
        os.remove(path)

def replace(srcPath, dstPath):
    if E(srcPath):
        os.replace(srcPath, dstPath)

def readInt(stream):
    return int(struct.unpack('>i' , stream.read(4))[0])

def writeInt(i, stream):
    stream.write(struct.pack('>i', i))

def readPacket(fileStream, fileSize):
    """
    Returns a packet tuple defining the next packet, and the timestamp or None, None if the stream has ended
    """
    numBytesLeft = fileSize - fileStream.tell()

    if numBytesLeft >=  8:
        timestamp = readInt(fileStream)
        length    = readInt(fileStream)
        if numBytesLeft >= 8 + length:
            return ((timestamp, length, fileStream), timestamp)

    return (None, -1)

def writePacket(packet, outputStream):
    timestamp, length, fileStream = packet
    writeInt(timestamp, outputStream)
    writeInt(length, outputStream)
    outputStream.write(fileStream.read(length))    

##################
#  Process File  #
##################

def processFile(path, writeResult = True):
    # 1. Ensure actions.tmcpr exists
    if (not E(J(path, ACTION_FILE))):
        if (not E(path)):
            print(path, " does not exist!")
        else:
            # print(J(path, ACTION_FILE), " does not exist!")
            print("Skipping", path)
        return

    actionFileSize = os.path.getsize(J(path, ACTION_FILE))
    recFileSize    = os.path.getsize(J(path, RECORDING_FILE)) 

    # 2. Zip the files based on timestamp
    with open(J(path, ACTION_FILE), 'rb')    as actionStream, \
         open(J(path, RECORDING_FILE), 'rb') as recStream,    \
         open(J(path, TEMP_FILE),'wb')       as output:

        actionPacket, actTimestamp = readPacket(actionStream, actionFileSize)
        recordingPacket, recTimestamp = readPacket(recStream, recFileSize)

        while ((not actionPacket is None) or (not recordingPacket is None)):
            if actTimestamp > 0 and (actTimestamp < recTimestamp or recTimestamp < 0):
                writePacket(actionPacket, output)
                actionPacket, actTimestamp = readPacket(actionStream, actionFileSize)
            else:
                writePacket(recordingPacket, output)
                recordingPacket, recTimestamp = readPacket(recStream, recFileSize)

    # 3. Replace recording file
    if (writeResult):
        replace(J(path, TEMP_FILE), J(path, RECORDING_FILE))
        #remove(J(path, ACTION_FILE))
    

#################
#     Main      #
#################

def main():
    """
    The main render script.
    """
    # Argument parsing
    parser = argparse.ArgumentParser(description='Merge actions.tmcpr into recording.tmcpr')
    parser.add_argument('files', metavar='/path/to/replay/folder/', type=str, nargs='+',
                    help='a list of paths to replay folders')
    parser.add_argument('--singleThreaded', dest='singleThreaded', action='store_const',
                    const=True, default=False,
                    help='Disable multi-threaded execution')
    parser.add_argument('--debug', dest='saveOutput', action='store_const',
                    const=False, default=True,
                    help='Disable modification - leave temp file instead of replacing recording.tmcpr')

    args = parser.parse_args()

    files = args.files
    singleThreaded = args.singleThreaded
    saveOutput = args.saveOutput

    if singleThreaded:
        for path in files:
            processFile(path)
    else:
        pool = Pool()
        pool.map(processFile, files)


if __name__ == "__main__":
    main()
