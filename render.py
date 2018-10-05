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
import os
import shutil
import sys
import glob
import numpy as np
import tqdm
import zipfile
import subprocess
import json
import time
import pyautogui
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
MERGED_DIR = J(WORKING_DIR, "merged")
RENDER_DIR = J(WORKING_DIR, "rendered_new")
MINECRAFT_DIR = J('/', 'home', 'hero', 'minecraft')
RECORDING_PATH = J(MINECRAFT_DIR, 'replay_recordings')
RENDERED_VIDEO_PATH = J(MINECRAFT_DIR, 'replay_videos')
RENDERED_LOG_PATH  =  J(MINECRAFT_DIR,  'replay_logs')
FINISHED_FILE = J(MINECRAFT_DIR, 'finished.txt')
LOG_FILE = J(J(MINECRAFT_DIR, 'logs'), 'debug.log')  # RAH
EOF_EXCEP_DIR = J(WORKING_DIR, 'EOFExceptions')
ZEROLEN_DIR = J(WORKING_DIR, 'zeroLengthFiles')
NULL_PTR_EXCEP_DIR = J(WORKING_DIR, 'nullPointerExceptions')

MC_LAUNCHER = '/home/hero/minecraft/launch.sh'
# MC_JAR = # This seems to be excluded from the current launcher
# MC_LAUNCH_ARGS = '-Xmx4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M'
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
    if not E(RENDER_DIR):
        os.makedirs(RENDER_DIR)
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


def render_metadata(renders: list) -> list:
    """
    Unpacks the metadata of a recording and checks its validity.
    """
    good_renders = []
    bad_renders = []

    for recording_name, render_path in tqdm.tqdm(renders):
        if E(render_path):
            # Check if metadata has already been extracted.
            if (E(J(render_path, GOOD_MARKER_NAME)) or
                    E(J(render_path,  BAD_MARKER_NAME))):
                # If it has been computed see if it is valid
                # or not.
                if E(J(render_path, GOOD_MARKER_NAME)):
                    good_renders.append((recording_name, render_path))
                else:
                    bad_renders.append((recording_name, render_path))
            else:
                try:
                    recording = get_recording_archive(recording_name)

                    def extract(fname): return recording.extract(
                        fname, render_path)

                    # Test end of stream validity.
                    #with open(extract(END_OF_STREAM), 'r') as eos:
                    #    assert len(eos.read()) > 0

                    # If everything is good extfct the metadata.
                    for mfile in METADATA_FILES:
                        assert str(mfile) in [str(x)
                                              for x in recording.namelist()]
                        extract(mfile)

                    # check that stream_meta_data is good
                    with open(J(render_path, 'metaData.json'), 'r') as f:
#                        print(render_path)
                        jbos = json.load(f)
                        assert (jbos["duration"] > 60000 or jbos["duration"] == 0)

                    # check that stream_meta_data is good
                    with open(J(render_path, 'stream_meta_data.json'), 'r') as f:
                        jbos = json.load(f)
                        assert jbos["has_EOF"]
                        assert not jbos["miss_seq_num"]

                    touch(J(render_path, GOOD_MARKER_NAME))
                    good_renders.append((recording_name, render_path))
                except (json.decoder.JSONDecodeError, AssertionError) as e:
                    _, _, tb = sys.exc_info()
                    traceback.print_tb(tb) # Fixed format
                    # Mark that this is a bad file.
                    touch(J(render_path, BAD_MARKER_NAME))
                    remove(J(render_path, GOOD_MARKER_NAME))
                    bad_renders.append((recording_name, render_path))

    return good_renders, bad_renders

# 2.Renders the actions.


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

# 3.Render the video encodings

# RAH - Kill MC (or any process) given the PID
def killMC(pid):
    process = psutil.Process(int(pid))
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

# RAH Launch MC - return the process so we can kill later if needed
def launchMC():
    # Run the Mine Craft Launcher
    p = subprocess.Popen(
        MC_LAUNCHER)#, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Launched ", MC_LAUNCHER)

    # x = 388
    # y = 626
    # print("Launching Minecraft: ", end='', flush=True)
    # pyautogui.moveTo(x, y)
    # delay = 5
    # for i in range(delay):
    #     print(delay-i, ' ', end='', flush=True)
    #     time.sleep(1)
    # print("0")

    # # Click on the launcher button that starts Minecraft
    # pyautogui.click(x, y)
    # print("\tWaiting for it to load:", end='', flush=True)
    # pyautogui.click(x, y)  # Click on the launcher button that starts Minecraft
    # delay = 5
    # for i in range(delay):
    #     print((delay-i) * 5, '', end='', flush=True)
    #     time.sleep(5)
    # print("0")
    time.sleep(10)
    return p


def launchReplayViewer():
    x = 860  # 1782
    y = 700  # 1172
    #pyautogui.moveTo(x, y)
    print("\tLaunching ReplayViewer: ", end='', flush=True)
    delay = 5
    for i in range(delay):
        print(delay-i, '', end='', flush=True)
        time.sleep(1)
    print("0")
    #pyautogui.click(x, y)  # Then click the button that launches replayMod


def render_videos(renders: list):
    """
    For every render directory, we render the videos.
    This works by:
     1) Copying the file to the minecraft directory
     2) Waiting for user input:
                    User render the video using replay mod and hit enter once the video is rendered
     3) Copying the produced mp4 to the rendered directory

    """
    # Restart minecraft after so many renders
    maxConsecutiveRenders = 8
    numSuccessfulRenders = 0

    # Remove any finished file flags to prevent against copying unfinished renders
    try:
        os.remove(FINISHED_FILE)
    except FileNotFoundError:
        pass

    # Clear recording directory to protect against crash messages
    for messyFile in glob.glob(J(RECORDING_PATH, '*')):
        try:
            os.remove(messyFile)
        except IsADirectoryError:
            shutil.rmtree(messyFile)

    p = launchMC()  # RAH launchMC() now returns subprocess - use p.PID to get process ID
    for recording_name, render_path in tqdm.tqdm(renders):
        # Get mcpr file from merged
        print("Rendering:", recording_name, '...')

        # Skip if the folder has an recording already
        # * means all if need specific format then *.csv
        list_of_files = glob.glob(J(render_path, '*.mp4'))
        if len(list_of_files):
            print("\tSkipping: replay folder contains", list_of_files[0])
            continue

        # Skip if the file has been skipped allready
        skip_path = J(render_path, SKIPPED_RENDER_FLAG)
        if E(skip_path):
            print("\tSkipping: file was previously skipped")
            continue

        mcpr_path = J(MERGED_DIR, (recording_name + ".mcpr"))

        copyfile(mcpr_path, J(RECORDING_PATH, (recording_name + ".mcpr")))
        copy_time = os.path.getmtime(
            J(RECORDING_PATH, (recording_name + ".mcpr")))

        # Presses the ReplayViewer() button - this step can be automated in the code, but this is cleaner
        launchReplayViewer()
        logFile = open(LOG_FILE, 'r', os.O_NONBLOCK)
        lineCounter = 0  # RAH So we can print line number of the error

        # Wait for completion (it creates a finished.txt file)
        video_path = None
        notFound = True
        while notFound:
            if os.path.exists(FINISHED_FILE):
                os.remove(FINISHED_FILE)
                notFound = False
                numSuccessfulRenders += 1
                if(numSuccessfulRenders > maxConsecutiveRenders):
                    killMC(p.pid)
                    time.sleep(5)
                    p = launchMC()
            else:
                # RAH Begin - this could be cleaner
                logLine = logFile.readline()
                if len(logLine) > 0:
                    lineCounter += 1
                    m = re.search(r"java.io.EOFException:", logLine)
                    if m:
                        print("\tline {}: {}".format(lineCounter, logLine))
                        print("\tfound java.io.EOFException")
                        killMC(p.pid)
                        time.sleep(5)  # Give the OS time to release this file
                        try:
                            os.rename(J(RECORDING_PATH, recording_name+'.mcpr'),
                                      J(EOF_EXCEP_DIR, recording_name+'.mcpr'))
                            shutil.copy(LOG_FILE,                               J(
                                EOF_EXCEP_DIR, recording_name+'.log'))
                        except:
                            pass
                        try:
                            shutil.rmtree(
                                J(RECORDING_PATH, recording_name+'.mcpr.tmp'))
                        except:
                            pass

                        p = launchMC()
                        break  # Exit the current file processing loop and process the next file

                    m = re.search(
                        r"Adding time keyframe at \d+ time -\d+", logLine)
                    if m:
                        print("\tline {}: {}".format(lineCounter, logLine))
                        print("\tfound 0 length file")
                        killMC(p.pid)
                        time.sleep(15)  # Give the OS time to release this file
                        try:
                            os.rename(J(RECORDING_PATH, recording_name+'.mcpr'),
                                      J(ZEROLEN_DIR, recording_name+'.mcpr'))
                            shutil.copy(LOG_FILE,                               J(
                                ZEROLEN_DIR, recording_name+'.log'))
                        except:
                            pass
                        try:
                            shutil.rmtree(J(RECORDING_PATH, recording_name+'.mcpr.tmp'))
                            with open(skip_path, 'a'):
                                try:
                                    os.utime(skip_path, None)  # => Set skip time to now
                                except OSError:
                                    pass  # File deleted between open() and os.utime() calls
                        except:
                            pass
                        p = launchMC()
                        break  # Exit the current file processing loop and process the next file

                    m = re.search(r"java.lang.NullPointerException", logLine)
                    if m:
                        print("\tline {}: {}".format(lineCounter, logLine),)
                        print("\tNullPointerException")
                        killMC(p.pid)
                        # Give the OS time to release this file nullPointerException needs more time than others
                        time.sleep(20)
                        print(J(RECORDING_PATH, recording_name+'.mcpr'),
                              J(NULL_PTR_EXCEP_DIR, recording_name+'.mcpr'))
                        try:
                            os.rename(J(RECORDING_PATH, recording_name+'.mcpr'),
                                      J(NULL_PTR_EXCEP_DIR, recording_name+'.mcpr'))
                            shutil.copy(LOG_FILE,                               J(
                                NULL_PTR_EXCEP_DIR, recording_name+'.log'))
                        except:
                            pass
                        try:
                            shutil.rmtree(
                                J(RECORDING_PATH, recording_name+'.mcpr.tmp'))
                            with open(skip_path, 'a'):
                                try:
                                    os.utime(skip_path, None)  # => Set skip time to now
                                except OSError:
                                    pass  # File deleted between open() and os.utime() calls
                        except:
                            pass
                        p = launchMC()
                        break  # Exit the current file processing loop and process the next file
        # RAH End

        # * means all if need specific format then *.cs
        list_of_files = glob.glob( J(RENDERED_VIDEO_PATH, '*.mp4'))
        # GET RECORDING
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

        # GET UNIVERSAL ACTION FORMAT SHIT.
        list_of_logs = glob.glob( J(RENDERED_LOG_PATH, '*.json'))
        if len(list_of_logs) > 0:
            # Check that this render was created after we copied
            log_path = max(list_of_logs, key=os.path.getmtime)
            if os.path.getmtime(log_path) < copy_time:
                print("\tError! Rendered log! is older than replay!")
                # user_input = input("Are you sure you want to copy this out of date render? (y/n)")
                # if "y" in user_input:
                #       print("using out of date recording")
                # else:
                print("\tskipping out of date rendering")
                log_path = None

        # GET new markers.json SHIT.
        list_of_logs = glob.glob( J(RENDERED_VIDEO_PATH, '*.json'))
        if len(list_of_logs) > 0:
            # Check that this render was created after we copied
            marker_path = max(list_of_logs, key=os.path.getmtime)
            if os.path.getmtime(marker_path) < copy_time:
                print("\tError! Rendered log! is older than replay!")
                # user_input = input("Are you sure you want to copy this out of date render? (y/n)")
                # if "y" in user_input:
                #       print("using out of date recording")
                # else:
                print("\tskipping out of date rendering")
                marker_path = None


        if not video_path is None and not log_path is None and not marker_path is None:
            print("\tCopying file", video_path, '==>\n\t',
                  render_path, 'created', os.path.getmtime(video_path))
            os.rename(video_path, J(render_path, 'recording.mp4'))
            print("\tCopying file", log_path, '==>\n\t',
                  render_path, 'created', os.path.getmtime(log_path))
            os.rename(log_path, J(render_path, 'univ.json'))

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
            print("\tNo Video file found")
            print("\tSkipping this file in the future")
            with open(skip_path, 'a'):
                try:
                    os.utime(skip_path, None)  # => Set skip time to now
                except OSError:
                    pass  # File deleted between open() and os.utime() calls
                # Remove mcpr file from dir
        try:
            os.remove(J(RECORDING_PATH, (recording_name + ".mcpr")))
        except:
            pass
    killMC(p.pid)


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
    render_videos(valid_renders)

    # from IPython import embed; embed()


if __name__ == "__main__":
    main()
