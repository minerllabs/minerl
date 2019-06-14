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
import functools
import multiprocessing
import os
import random
import shutil
import sys
import glob
import numpy as np
import tqdm
import zipfile
import subprocess
import json
import time
import shutil
import psutil
import traceback
import re
from shutil import copyfile

# 3
# UTILITIES
#######################
J = os.path.join
E = os.path.exists
WORKING_DIR = "output"
MERGED_DIR = J(WORKING_DIR, "merged_new")
RENDER_DIR = J(WORKING_DIR, "rendered_new")

# Minecraft Files
NUM_MINECRAFT_DIR = 4
MINECRAFT_DIR = [J('/', 'home', 'hero', 'minecraft_{}'.format(i)) for i in range(NUM_MINECRAFT_DIR)]
RECORDING_PATH = [J(d, 'replay_recordings') for d in MINECRAFT_DIR]
RENDERED_VIDEO_PATH = [J(d, 'replay_videos') for d in MINECRAFT_DIR]
RENDERED_LOG_PATH = [J(d,  'replay_logs') for d in MINECRAFT_DIR]
FINISHED_FILE = [J(d, 'finished.txt') for d in MINECRAFT_DIR]
LOG_FILE = [J(d, 'logs', 'debug.log') for d in MINECRAFT_DIR]
MC_LAUNCHER = [J(d, 'launch.sh') for d in MINECRAFT_DIR]

# Error directories
ERROR_PARENT_DIR = J(WORKING_DIR, 'error_logs')
EOF_EXCEP_DIR = J(ERROR_PARENT_DIR, 'end_of_file_reached')
ZEROLEN_DIR = J(ERROR_PARENT_DIR, 'zero_length')
NULL_PTR_EXCEP_DIR = J(ERROR_PARENT_DIR, 'null_pointer_except')
ZIP_ERROR_DIR = J(ERROR_PARENT_DIR, 'zip_file')
MISSING_RENDER_OUTPUT = J(ERROR_PARENT_DIR, 'missing_output')

BLACKLIST_PATH = J(WORKING_DIR, "blacklist.txt")

END_OF_STREAM = 'end_of_stream.txt'
ACTION_FILE = "actions.tmcpr"
BAD_MARKER_NAME, GOOD_MARKER_NAME = 'INVALID', 'VALID'
SKIPPED_RENDER_FLAG = 'SKIPPED_RENDER'

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


def get_recording_archive(recording_name):
    """
    Gets the zipfile object of a mcpr recording.
    """
    mcpr_path = J(MERGED_DIR, (recording_name + ".mcpr"))
    assert E(mcpr_path)

    return zipfile.ZipFile(mcpr_path)

##################
# PIPELINE
#################

# 1. Construct render working dirs.


def construct_render_dirs(blacklist):
    """
    Constructs the render directories omitting
    elements on a blacklist.
    """

    dirs = [RENDER_DIR,
        ERROR_PARENT_DIR,
        EOF_EXCEP_DIR,
        ZEROLEN_DIR,
        NULL_PTR_EXCEP_DIR,
        ZIP_ERROR_DIR,
        MISSING_RENDER_OUTPUT]

    for dir in dirs:
        if not E(dir):
            os.makedirs(dir)       


    # We only care about unrendered directories.
    render_dirs = []

    for filename in tqdm.tqdm(os.listdir(MERGED_DIR)):
        if filename.endswith(".mcpr") and filename not in blacklist:
            recording_name = filename.split(".mcpr")[0]
            render_path = J(RENDER_DIR, recording_name)
            print(render_path)
            if not E(render_path):
                os.makedirs(render_path)

            render_dirs.append((recording_name, render_path))

    return render_dirs


# 2. render metadata from the files.
def render_metadata(renders: list):
    """
    Unpacks the metadata of a recording and checks its validity.
    """
    good_renders = []
    bad_renders = []

    for recording_name, render_path in tqdm.tqdm(renders):
        if E(render_path):
            # Check if metadata has already been extracted.
            # if (E(J(render_path, GOOD_MARKER_NAME)) or
            #         E(J(render_path,  BAD_MARKER_NAME))):
            #     # If it has been computed see if it is valid
            #     # or not.
            #     if E(J(render_path, GOOD_MARKER_NAME)):
            #         good_renders.append((recording_name, render_path))
            #     else:
            #         bad_renders.append((recording_name, render_path))
            # else:
            # BAH check metadata each time
            if True:
                try:
                    recording = get_recording_archive(recording_name)

                    def extract(fname): return recording.extract(
                        fname, render_path)

                    # If everything is good extract the metadata.
                    for mfile in METADATA_FILES:
                        assert str(mfile) in [str(x) for x in recording.namelist()]
                        if not E(J(render_path, mfile)):
                            extract(mfile)

                    # check that stream_meta_data is good
                    with open(J(render_path, 'metaData.json'), 'r') as f:
                        # print(render_path)
                        jbos = json.load(f)
                        # assert (ile["duration"] > 60000 or jbos["duration"] == 0)
                        assert (jbos["duration"] > 300000)

                    # check that stream_meta_data is good
                    with open(J(render_path, 'stream_meta_data.json'), 'r') as f:
                        jbos = json.load(f)
                        assert jbos["has_EOF"]
                        assert not jbos["miss_seq_num"]

                    touch(J(render_path, GOOD_MARKER_NAME))
                    remove(J(render_path, BAD_MARKER_NAME))
                    good_renders.append((recording_name, render_path))
                except (json.decoder.JSONDecodeError, AssertionError):
                    _, _, tb = sys.exc_info()
                    traceback.print_tb(tb)  # Fixed format
                    # Mark that this is a bad file.
                    touch(J(render_path, BAD_MARKER_NAME))
                    remove(J(render_path, GOOD_MARKER_NAME))
                    bad_renders.append((recording_name, render_path))

    return good_renders, bad_renders


# 3.Renders the actions.
def render_actions(renders: list):
    """
    For every render directory, we render the actions
    """
    good_renders = []
    bad_renders = []

    for recording_name, render_path in tqdm.tqdm(renders):
        if E(J(render_path, 'network.npy')):
            if E(J(render_path, GOOD_MARKER_NAME)):
                good_renders.append((recording_name, render_path))
            else:
                bad_renders.append((recording_name, render_path))
        else:
            try:
                recording = get_recording_archive(recording_name)

                def extract(fname): return recording.extract(
                    fname, render_path)

                # Extract actions
                assert str(ACTION_FILE) in [str(x)
                                            for x in recording.namelist()]
                # Extract it if it doesnt exist
                action_mcbr = extract(ACTION_FILE)
                # Check that it's not-empty.
                assert not os.stat(action_mcbr).st_size == 0

                # Run the actual parse action and make sure that its actually of length 0.
                p = subprocess.Popen(["python3", "parse_action.py", os.path.abspath(
                    action_mcbr)], cwd='action_rendering')
                returncode = (p.wait())
                assert returncode == 0

                good_renders.append((recording_name, render_path))
            except AssertionError as e:
                _, _, tb = sys.exc_info()
                traceback.print_tb(tb) # Fixed format
                touch(J(render_path, BAD_MARKER_NAME))
                remove(J(render_path, GOOD_MARKER_NAME))
                bad_renders.append((recording_name, render_path))

    return good_renders, bad_renders


# Kill MC (or any process) given the PID
def killMC(process):
    for proc in psutil.Process(int(process.pid)).children(recursive=True):
        try:
            proc.kill()
        except psutil.NoSuchProcess:
            pass
    try:
        process.kill()
    except psutil.NoSuchProcess:
        pass


# Launch MC - return the process so we can kill later if needed
def launchMC(index=0):
    # Run the Mine Craft Launcher
    p = subprocess.Popen(
        MC_LAUNCHER, cwd=MINECRAFT_DIR[index])#, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Launched ", MC_LAUNCHER)

    #Give Minecraft time to load
    # time.sleep(10)
    return p


def logError(errorDIR, recording_name, skip_path, index=0):
    try:
        shutil.move(J(RECORDING_PATH[index], recording_name+'.mcpr'),
                    J(errorDIR, recording_name+'.mcpr'))
        shutil.copy(LOG_FILE[index], J(errorDIR, recording_name+'.log'))
    except:
        pass
    try:
        shutil.rmtree(J(RECORDING_PATH[index], recording_name+'.mcpr.tmp'))
        with open(skip_path, 'a'):
            try:
                os.utime(skip_path, None)  # => Set skip time to now
            except OSError:
                pass  # File deleted between open() and os.utime() calls
    except:
        pass


def relaunchMC(p, errorDIR, recording_name, skip_path, index=0):
    killMC(p)
    # time.sleep(15)  # Give the OS time to release this file
    logError(errorDIR, recording_name, skip_path)
    return launchMC(index)


# 4.Render the videos
def _render_videos(manager, file, debug=False):
    n = manager.get_index()
    ret = render_videos(file, index=n, debug=debug)
    manager.free_index(n)
    return ret


def render_videos(render: tuple[str, str], index=0):
    """
    For every render directory, we render the videos.
    This works by:
     1) Copying the file to the minecraft directory
     2) Waiting for user input:
                    User render the video using replay mod and hit enter once the video is rendered
     3) Copying the produced mp4 to the rendered directory

    """
    # Restart minecraft after so many renders
    maxConsecutiveRenders = 1
    numSuccessfulRenders = 0

    # Remove any finished file flags to prevent against copying unfinished renders
    try:
        os.remove(FINISHED_FILE[index])
    except FileNotFoundError:
        pass

    # Clear recording directory to protect against crash messages
    for messyFile in glob.glob(J(RECORDING_PATH[index], '*')):
        try:
            os.remove(messyFile)
        except IsADirectoryError:
            shutil.rmtree(messyFile)

    p = launchMC()
    try:
        recording_name, render_path = render

        # Get mcpr file from merged
        tqdm.tqdm.write("Rendering {} ...".format(recording_name))

        # Skip if the folder has an recording already
        # * means all if need specific format then *.csv
        list_of_files = glob.glob(J(render_path, '*.mp4'))
        if len(list_of_files):
            tqdm.tqdm.write("\tSkipping: replay folder contains {}".format(list_of_files[0]))
            return 0

        # Skip if the file has been skipped already
        skip_path = J(render_path, SKIPPED_RENDER_FLAG)
        if E(skip_path):
            tqdm.tqdm.write("\tSkipping: file was previously skipped")
            return 0

        mcpr_path = J(MERGED_DIR, (recording_name + ".mcpr"))

        copyfile(mcpr_path, J(RECORDING_PATH[index], (recording_name + ".mcpr")))
        copy_time = os.path.getmtime(
            J(RECORDING_PATH[index], (recording_name + ".mcpr")))

        logFile = open(LOG_FILE[index], 'r', os.O_NONBLOCK)
        lineCounter = 0  # RAH So we can print line number of the error

        # Wait for completion (it creates a finished.txt file)
        video_path = None
        notFound = True
        while notFound:
            if os.path.exists(FINISHED_FILE[index]) or p.poll() is not None:
                if os.path.exists(FINISHED_FILE[index]):
                    os.remove(FINISHED_FILE[index])
                try:
                    print("Waiting for Minecraft to close")
                    p.wait(400)
                    print("Minecraft closed")
                except TimeoutError:
                    print("Timeout")
                    p.kill()
                    # killMC(p)
                except:
                    print("Error stopping")
                p = launchMC()

                notFound = False
                numSuccessfulRenders += 1
                # if(numSuccessfulRenders > maxConsecutiveRenders):
                #     killMC(p)
                #     numSuccessfullRenders = 0
                #     # time.sleep(5)
                #     p = launchMC()
            else:
                logLine = logFile.readline()
                if len(logLine) > 0:
                    lineCounter += 1
                    errorDir = None
                    if re.search(r"EOFException:", logLine):
                        print("\tfound java.io.EOFException")
                        errorDir = EOF_EXCEP_DIR

                    elif re.search(r"Adding time keyframe at \d+ time -\d+", logLine):
                        print("\tfound 0 length file")
                        errorDir = ZEROLEN_DIR

                    elif re.search(r"NullPointerException", logLine):
                        print("\tNullPointerException")
                        errorDir = NULL_PTR_EXCEP_DIR

                    elif re.search(r"zip error", logLine):
                        print('ZIP file error')
                        errorDir = ZIP_ERROR_DIR
                    
                    if not errorDir is None:
                        print("\tline {}: {}".format(lineCounter, logLine))
                        p = relaunchMC(p, errorDir, recording_name, skip_path)
                        break
            time.sleep(0.1)

        logFile.close()
        if notFound:
            try:
                os.remove(J(RECORDING_PATH[index], (recording_name + ".mcpr")))
            except:
                pass
            return 0

        video_path = None
        log_path = None
        marker_path = None

        # GET RECORDING
        list_of_files = glob.glob( J(RENDERED_VIDEO_PATH[index], '*.mp4'))
        if len(list_of_files) > 0:
            # Check that this render was created after we copied
            video_path = max(list_of_files, key=os.path.getmtime)
            if os.path.getmtime(video_path) < copy_time:
                print("\tError! Rendered file is older than replay!")
                # user_input = input("Are you sure you want to copy this out of date render? (y/n)")
                # if "y" in user_input:
                #       print("using out of date recording")
                # else:
                print("\tskipping out of date rendering")
                video_path = None

        # GET UNIVERSAL ACTION FORMAT
        list_of_logs = glob.glob(J(RENDERED_LOG_PATH[index], '*.json'))
        if len(list_of_logs) > 0:
            # Check that this render was created after we copied
            log_path = max(list_of_logs, key=os.path.getmtime)
            if os.path.getmtime(log_path) < copy_time:
                print("\tError! Rendered log is older than replay!")
                # user_input = input("Are you sure you want to copy this out of date render? (y/n)")
                # if "y" in user_input:
                #       print("using out of date action json")
                # else:
                print("\tskipping out of date action json")
                log_path = None

        # GET new markers.json
        list_of_logs = glob.glob(J(RENDERED_VIDEO_PATH[index], '*.json'))
        if len(list_of_logs) > 0:
            # Check that this render was created after we copied
            marker_path = max(list_of_logs, key=os.path.getmtime)
            if os.path.getmtime(marker_path) < copy_time:
                print("\tError! markers.json is older than replay!")
                # user_input = input("Are you sure you want to copy this out of date render? (y/n)")
                # if "y" in user_input:
                #       print("using out of date recording")
                # else:
                print("\tskipping out of date markers.json")
                marker_path = None

        if not video_path is None and not log_path is None and not marker_path is None:
            print("\tCopying file", video_path, '==>\n\t',
                  render_path, 'created', os.path.getmtime(video_path))
            shutil.move(video_path, J(render_path, 'recording.mp4'))
            print("\tCopying file", log_path, '==>\n\t',
                  render_path, 'created', os.path.getmtime(log_path))
            shutil.move(log_path, J(render_path, 'univ.json'))

            print("\tRecording start and stop timestamp for video")
            metadata = json.load(open(J(render_path, 'stream_meta_data.json')))
            videoFilename = video_path.split('/')[-1]

            metadata['start_timestamp'] = int(videoFilename.split('_')[1])
            metadata['stop_timestamp'] = int(
                videoFilename.split('_')[2].split('-')[0])
            with open(marker_path) as markerFile:
                metadata['markers'] = json.load(markerFile)
            json.dump(metadata, open(
                J(render_path, 'stream_meta_data.json'), 'w'))
        else:
            print("\tMissing one or more file")
            print("\tSkipping this file in the future")
            logError(MISSING_RENDER_OUTPUT, recording_name, skip_path)

        # Remove mcpr file from dir
        try:
            os.remove(J(RECORDING_PATH[index], (recording_name + ".mcpr")))
        except:
            pass
    finally:
        killMC(p.pid)
    return 1


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
                    return index + self.first_index
                else:
                    time.sleep(0.01)

    def free_index(self, i):
        with self.worker_lock:
            self.workers[i - self.first_index] -= 1

def main():
    """
    The main render script.
    """
    # 1. Load the blacklist.
    blacklist = set(np.loadtxt(BLACKLIST_PATH, dtype=np.str).tolist())

    print("Constructing render directories.")
    renders = construct_render_dirs(blacklist)

    print("Validating metadata from files:")
    valid_renders, invalid_renders = render_metadata(renders)
    print(len(valid_renders))
    # print("Rendering actions: ")
    # valid_renders, invalid_renders = render_actions(valid_renders)
    print("... found {} valid recordings and {} invalid recordings"
          " out of {} total files".format(
              len(valid_renders), len(invalid_renders), len(os.listdir(MERGED_DIR)))
          )
    print("Rendering videos: ")
    # render_videos(valid_renders)

    # Render videos in multiprocessing queue
    multiprocessing.freeze_support()
    with multiprocessing.Pool(
            NUM_MINECRAFT_DIR, initializer=tqdm.tqdm.set_lock, initargs=(multiprocessing.RLock(),)) as pool:
        manager = ThreadManager(multiprocessing.Manager(), NUM_MINECRAFT_DIR, 0, 1)
        func = functools.partial(_render_videos, manager)
        num_rendered = list(
            tqdm.tqdm(pool.imap_unordered(func, valid_renders), total=len(valid_renders), desc='Files', miniters=1,
                      position=0, maxinterval=1))

    print('Rendered {} new files!'.format(num_rendered))

    # from IPython import embed; embed()


if __name__ == "__main__":
    main()
