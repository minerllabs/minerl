# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
"""
Merges raw binary packet data from each "player stream" into compressed zip archives
(MCPR files). Uses 7z, which has the best compression ratios on the market, for zipping.

Requirements:
    * 7z: You can install `7z` on Ubuntu with `sudo apt install p7zip`.
    * Run `download2.sh` first to get the trajectories to compress.
"""

import contextlib
import os
import pathlib
import shutil
import tqdm
import glob
import subprocess
import tempfile
import struct
import time
import multiprocessing
import numpy as np
import io
import argparse

from subprocess import STDOUT

from minerl.data.util.constants import (
    MERGED_DIR,
    BLACKLIST_TXT,
    PARSE_COMMAND,
    Z7_COMMAND,
    TEMP_ROOT,
    BLOCK_SIZE,
    ACTION_FILE,
    RECORDING_FILE,
    GLOB_STR_BASE
)

from minerl.data.util.constants import OUTPUT_DIR as WORKING_DIR
from minerl.data.util.constants import DOWNLOAD_DIR as DOWNLOADED_DIR

try:
    from subprocess import DEVNULL  # py3k
except ImportError:
    import os

    DEVNULL = open(os.devnull, 'wb')

J = os.path.join
E = os.path.exists


def remove(path):
    if E(path):
        os.remove(path)


def replace(srcPath, dstPath):
    if E(srcPath):
        os.replace(srcPath, dstPath)


def readInt(stream):
    return int(struct.unpack('>i', stream.read(4))[0])


def writeInt(i, stream):
    stream.write(struct.pack('>i', i))


def readPacket(fileStream, fileSize):
    """
    Returns a packet tuple defining the next packet, and the timestamp or None, None if the stream has ended
    """
    numBytesLeft = fileSize - fileStream.tell()

    if numBytesLeft >= 8:
        timestamp = readInt(fileStream)
        length = readInt(fileStream)
        if numBytesLeft >= 8 + length:
            return ((timestamp, length, fileStream), timestamp)

    return (None, -1)


def writePacket(packet, outputStream):
    timestamp, length, fileStream = packet
    writeInt(timestamp, outputStream)
    writeInt(length, outputStream)
    outputStream.write(fileStream.read(length))


def read_buffer(file_stream):
    return io.BytesIO(file_stream.read())


##################
#  Process File  #
##################

def processFile(path, writeResult=True):
    # 1. Ensure actions.tmcpr exists
    if (not E(J(path, ACTION_FILE))):
        # if (not E(path)):
        # print(path, " does not exist!")
        # else:
        # print("Skipping", path)
        return False

    actionFileSize = os.path.getsize(J(path, ACTION_FILE))
    recFileSize = os.path.getsize(J(path, RECORDING_FILE))

    # 2. Zip the files based on timestamp
    with open(J(path, ACTION_FILE), 'rb')    as actionStream, \
            open(J(path, RECORDING_FILE), 'rb') as recStream:

        actionStream = read_buffer(actionStream)
        recStream = read_buffer(recStream)
        output = io.BytesIO()

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
        with open(J(path, RECORDING_FILE), 'wb') as f:
            f.write(output.getvalue())
        # replace(J(path, TEMP_FILE), J(path, RECORDING_FILE))
        remove(J(path, ACTION_FILE))

    return True


def touch(fname):
    path = pathlib.Path(fname)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()


def concat(infiles, outfile):
    touch(outfile)
    if hasattr(os, 'O_BINARY'):
        o_binary = getattr(os, 'O_BINARY')
    else:
        o_binary = 0
    output_file = os.open(outfile, os.O_WRONLY | o_binary)
    for input_filename in infiles:
        input_file = os.open(input_filename, os.O_RDONLY | o_binary)
        while True:
            input_block = os.read(input_file, BLOCK_SIZE)
            if not input_block:
                break
            os.write(output_file, input_block)
        os.close(input_file)
    os.close(output_file)


def get_files_to_merge(blacklist):
    files_to_merge = []
    downloaded_streams = list(glob.glob(J(GLOB_STR_BASE, "player*")))
    for f in tqdm.tqdm(downloaded_streams):
        try:
            assert os.path.isfile(f), "{} was not a file. Your download dir could be wrong."
            name = os.path.basename(f)
            delimited_name = name.split("-")
            who, version = delimited_name[0], delimited_name[1]
            stream_name = "{}-{}".format(who, version)

            # if ( not  E(J(MERGED_DIR, "{}.mcpr".format(stream_name))) 
            #     and not (stream_name in blacklist)):
            files_to_merge.append(stream_name)

        except AssertionError as e:
            print("FAILED", e)
            # raise
    return list(set(files_to_merge))


def merge_stream(stream_name):
    # 1. Concatenate files.
    # 2. Merge files.
    # 3. 7z files
    # 4. Place files
    os.makedirs(TEMP_ROOT, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as tempdir:
        target_name = J(MERGED_DIR, "{}.mcpr".format(stream_name))
        bin_name = J(tempdir, "{}.bin".format(stream_name))
        # Concatenate
        shards = sorted(glob.glob(J(GLOB_STR_BASE, "{}-*".format(stream_name))))

        # print(shards)
        t0 = time.time()
        try:
            concat(shards, bin_name)
        except OSError:
            print(f"FAILED_TO_CONCAT {stream_name}")
            return "Failed to concat", stream_name

        # Parse
        results_dir = J(tempdir, 'result')
        if not E(results_dir):
            os.makedirs(results_dir)
        proc = subprocess.Popen(PARSE_COMMAND + [bin_name], cwd=tempdir, stdout=DEVNULL, stderr=STDOUT)
        parse_success = (proc.wait() == 0)

        if parse_success:
            if processFile(results_dir):
                zip_file = "{}.zip".format(stream_name)
                mcpr_file = "{}.mcpr".format(stream_name)
                proc = subprocess.Popen(
                    Z7_COMMAND + ["a", zip_file, J(results_dir, "*")], cwd=tempdir, stdout=DEVNULL)
                proc.wait()
                os.rename(J(tempdir, zip_file), J(tempdir, mcpr_file))

                # Overwrite files.
                if E(J(MERGED_DIR, mcpr_file)):
                    os.remove(J(MERGED_DIR, mcpr_file))

                shutil.move(J(tempdir, mcpr_file), MERGED_DIR)

                return (time.time() - t0)
            else:
                print("FAILED_TO_ZIP {}".format(stream_name))
                return "FAILED to ZIP", stream_name
        else:
            print("FAILED_TO_PARSE {}".format(stream_name))
            return "FAILED TO PARSE", stream_name


def main(n_workers: int = 1, parallel: bool = True):
    """
    Args:
        parallel: If True, then use true multiprocessing to parallelize jobs. Otherwise,
            use multithreading which allows breakpoints and other debugging tools, but
            is slower.
    """
    assert E(DOWNLOADED_DIR), "No download directory! Be sure to have the downloaded files prepared:\n\t{}".format(
        DOWNLOADED_DIR)

    touch(BLACKLIST_TXT)
    with open(BLACKLIST_TXT, 'r') as f:
        blacklist = f.readlines()
        blacklist = [x.strip() for x in blacklist if x.strip()]

    files_to_merge = get_files_to_merge(blacklist)

    if not E(MERGED_DIR):
        os.makedirs(MERGED_DIR)

    # Now lets set up a multiprocessing pool
    # print(merge_stream(files_to_merge[0]))

    print("FOUND {} STREAMS TO MERGE.".format(len(files_to_merge)))
    print("BLACKLIST CONTAINS {} STREAMS.".format(len(blacklist)))
    if not files_to_merge:
        return

    if parallel:
        import multiprocessing
    else:
        import multiprocessing.dummy as multiprocessing

    with multiprocessing.Pool(n_workers, tqdm.tqdm.set_lock,
                              initargs=(multiprocessing.RLock(),)) as pool:
        timings = list(tqdm.tqdm(
            pool.imap_unordered(merge_stream, files_to_merge),
            total=len(files_to_merge), desc='Merging'))
        failed_streams = [x[1] for x in timings if isinstance(x, tuple)]
        times = np.array([x for x in timings if not isinstance(x, tuple)])

    # Write blacklist
    for f in (failed_streams):
        if f not in blacklist:
            blacklist.append(f)
    print(blacklist)
    with open(BLACKLIST_TXT, 'w') as f:
        f.write('\n'.join(blacklist))

    print("FINISHED WITH TIMINGS:")
    print("\t Number of streams succeeded:", len(times))
    print("\t Number of streams failed:", len(failed_streams))
    if times is not None and len(times) > 0:
        print("\t Average time: {}".format(times.mean()))


def main_console():
    """Like main, except it also reads arguments from stdin."""
    parser = argparse.ArgumentParser('Merge Script')
    parser.add_argument('num_workers', type=int, help='Number of parallel workers.')
    opts = parser.parse_args()
    main(n_workers=opts["num_workers"])


if __name__ == "__main__":
    main_console()
