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
from pathlib import Path
import re
from shutil import copyfile

from minerl.data.util.constants import (
    OUTPUT_DIR as WORKING_DIR,
    DOWNLOAD_DIR as DOWNLOADED_DIR,
    NUM_MINECRAFTS as NUM_MINECRAFT_DIR,
    RENDERERS_DIR,
)

# 3
# UTILITIES
#######################
from minerl.data.util.constants import (
    MERGED_DIR,
    RENDER_DIR,
    J,
    E
)

# RENDERERS:
from minerl.data.util.constants import (
    MINECRAFT_DIR,
    RECORDING_PATH,
    RENDERED_VIDEO_PATH,
    RENDERED_LOG_PATH,
    FINISHED_FILE,
    LOG_FILE,
    MC_LAUNCHER,
    RENDER_ONLY_EXPERIMENTS
)

# Error directories
from minerl.data.util.constants import (
    ERROR_PARENT_DIR,
    EOF_EXCEP_DIR,
    ZEROLEN_DIR,
    NULL_PTR_EXCEP_DIR,
    ZIP_ERROR_DIR,
    MISSING_RENDER_OUTPUT,
    OTHER_ERROR_DIR,
    X11_ERROR_DIR
)

from minerl.data.util.constants import (BLACKLIST_TXT as BLACKLIST_PATH)

from minerl.data.util.constants import (
    END_OF_STREAM,
    ACTION_FILE,
    BAD_MARKER_NAME, GOOD_MARKER_NAME,
    SKIPPED_RENDER_FLAG,
    METADATA_FILES,
    ThreadManager,
    touch,
    remove
)


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
            MISSING_RENDER_OUTPUT,
            X11_ERROR_DIR]

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

                    def extract(fname):
                        return recording.extract(
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

                        # go through and check if we got the experiments.

                    try:
                        with open(J(render_path, 'markers.json'), 'r') as f:
                            markers = json.load(f)
                            has_any_exps = False
                            for marker in markers:
                                exp_metadata = marker['value']['metadata']['expMetadata']

                                for exp in RENDER_ONLY_EXPERIMENTS:
                                    has_any_exps = (exp in exp_metadata) or has_any_exps

                            assert has_any_exps

                    except (KeyError, FileNotFoundError):
                        raise AssertionError("Couldn't open metadata json.")

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

                def extract(fname):
                    return recording.extract(
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
                traceback.print_tb(tb)  # Fixed format
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
def launchMC(index):
    # Run the Mine Craft Launcher
    p = subprocess.Popen(
        MC_LAUNCHER[index], cwd=MINECRAFT_DIR[index])  # , stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # print("Launched ", MC_LAUNCHER[index])

    # Give Minecraft time to load
    # time.sleep(10)
    return p


def logError(errorDIR, recording_name, skip_path, index):
    print("\t\tLogging error for {} in directory {}.".format(recording_name, errorDIR))
    try:
        shutil.move(J(RECORDING_PATH[index], recording_name + '.mcpr'),
                    J(errorDIR, recording_name + '.mcpr'))
    except Exception as e:
        print("\t\tERRROR", e)
        pass

    logFile = open(LOG_FILE[index], 'r', os.O_NONBLOCK).read()
    with open(J(errorDIR, recording_name + '.log'), 'w') as f:
        f.write(logFile)

    try:
        shutil.rmtree(J(RECORDING_PATH[index], recording_name + '.mcpr.tmp'))
    except Exception as e:
        print("\t\tERRROR s", e)
        pass

    with open(skip_path, 'a'):
        try:
            os.utime(skip_path, None)  # => Set skip time to now
        except OSError:
            pass  # File deleted between open() and os.utime() calls


def relaunchMC(p, errorDIR, recording_name, skip_path, index):
    killMC(p)
    # time.sleep(15)  # Give the OS time to release this file
    logError(errorDIR, recording_name, skip_path, index)
    return launchMC(index)


# 4.Render the videos
def _render_videos(manager, file, debug=True):
    n = manager.get_index()
    ret = render_videos(file, index=n, debug=debug)
    manager.free_index(n)
    return ret


def render_videos(render: tuple, index=0, debug=False):
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

    p = None
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

        if not E(LOG_FILE[index]):
            os.makedirs(os.path.dirname(LOG_FILE[index]), exist_ok=True)
            Path(LOG_FILE[index]).touch()

        logFile = open(LOG_FILE[index], 'r', os.O_NONBLOCK)
        lineCounter = 0  # RAH So we can print line number of the error

        # Render the file
        p = launchMC(index)

        # Wait for completion (it creates a finished.txt file)
        video_path = None
        notFound = True
        errorDir = None
        while notFound:
            if os.path.exists(FINISHED_FILE[index]) or p.poll() is not None:
                if os.path.exists(FINISHED_FILE[index]):
                    os.remove(FINISHED_FILE[index])

                    notFound = False
                    numSuccessfulRenders += 1
                else:
                    notFound = True

                try:
                    if debug:
                        print("Waiting for Minecraft to close")
                    p.wait(400)
                    if debug:
                        print("Minecraft closed")
                except TimeoutError:
                    tqdm.tqdm.write("Timeout")
                    p.kill()
                    # killMC(p)
                except:
                    tqdm.tqdm.write("Error stopping")
                # p = launchMC(index)

                # if(numSuccessfulRenders > maxConsecutiveRenders):
                #     killMC(p)
                #     numSuccessfulRenders = 0
                #     # time.sleep(5)
                #     p = launchMC()
                break
            else:
                logLine = logFile.readline()
                if len(logLine) > 0:
                    lineCounter += 1
                    if re.search(r"EOFException:", logLine):
                        if debug:
                            print("\tfound java.io.EOFException")
                        errorDir = EOF_EXCEP_DIR

                    elif re.search(r"Adding time keyframe at \d+ time -\d+", logLine):
                        if debug:
                            print("\tfound 0 length file")
                        errorDir = ZEROLEN_DIR

                    elif re.search(r"NullPointerException", logLine):
                        if not re.search(r'exceptionCaught', logLine):
                            if debug:
                                print("\tNullPointerException")
                            errorDir = NULL_PTR_EXCEP_DIR

                    elif re.search(r"zip error", logLine) or re.search(r"zip file close", logLine):
                        if debug:
                            print('ZIP file error')
                        errorDir = ZIP_ERROR_DIR

                    elif re.search(r'connect to X11 window server', logLine):
                        if debug:
                            print("X11 error")
                        errorDir = X11_ERROR_DIR
                    elif re.search(r'no lwjgl64 in java', logLine):
                        if debug:
                            print("missing lwjgl.")
                        errorDir = OTHER_ERROR_DIR

                    # elif re.search(r"Exception", logLine):
                    # if debug:
                    #     print("Unknown exception!!!")
                    # error_dir = OTHER_ERROR_DIR

                    if errorDir:
                        if debug:
                            print("\tline {}: {}".format(lineCounter, logLine))
                        break
                        # p = relaunchMC(p, errorDir, recording_name, skip_path)

        time.sleep(1)
        logFile.close()
        if errorDir:
            print(errorDir)
            logError(errorDir, recording_name, skip_path, index)
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
        list_of_files = glob.glob(J(RENDERED_VIDEO_PATH[index], '*.mp4'))
        if len(list_of_files) > 0:
            # Check that this render was created after we copied
            video_path = max(list_of_files, key=os.path.getmtime)
            if os.path.getmtime(video_path) < copy_time:
                if debug:
                    print("\tError! Rendered file is older than replay!")
                    print("\tskipping out of date rendering")
                video_path = None

        # GET UNIVERSAL ACTION FORMAT
        list_of_logs = glob.glob(J(RENDERED_LOG_PATH[index], '*.json'))
        if len(list_of_logs) > 0:
            # Check that this render was created after we copied
            log_path = max(list_of_logs, key=os.path.getmtime)
            if os.path.getmtime(log_path) < copy_time:
                if debug:
                    print("\tError! Rendered log is older than replay!")
                    print("\tskipping out of date action json")
                log_path = None

        # GET new markers.json
        list_of_logs = glob.glob(J(RENDERED_VIDEO_PATH[index], '*.json'))
        if len(list_of_logs) > 0:
            # Check that this render was created after we copied
            marker_path = max(list_of_logs, key=os.path.getmtime)
            if os.path.getmtime(marker_path) < copy_time:
                if debug:
                    print("\tError! markers.json is older than replay!")
                    print("\tskipping out of date markers.json")
                marker_path = None

        if not video_path is None and not log_path is None and not marker_path is None:
            if debug:
                print("\tCopying file", video_path, '==>\n\t',
                      render_path, 'created', os.path.getmtime(video_path))
            shutil.move(video_path, J(render_path, 'recording.mp4'))
            if debug:
                print("\tCopying file", log_path, '==>\n\t',
                      render_path, 'created', os.path.getmtime(log_path))
            shutil.move(log_path, J(render_path, 'univ.json'))

            if debug:
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
            if debug:
                print("\tMissing one or more file")
                print("\tSkipping this file in the future")
                print("\t{} {} {}".format(video_path, marker_path, log_path))
            logError(MISSING_RENDER_OUTPUT, recording_name, skip_path, index)
            try:
                os.remove(J(RECORDING_PATH[index], (recording_name + ".mcpr")))
            except:
                pass
            return 0

        # Remove mcpr file from dir
        try:
            os.remove(J(RECORDING_PATH[index], (recording_name + ".mcpr")))
        except:
            pass
    finally:
        if p is not None:
            try:
                p.wait(400)
            except (TimeoutError, subprocess.TimeoutExpired):
                p.kill()
            time.sleep(10)
    return 1


def clean_render_dirs():
    paths_to_clear = [RENDERED_VIDEO_PATH, RECORDING_PATH, RENDERED_LOG_PATH]
    for p in paths_to_clear:
        map(remove, [glob.glob(J(x, '*')) for x in p])
    pass


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
            len(valid_renders), len(invalid_renders), len(os.listdir(MERGED_DIR))))

    unfinished_renders = [v for v in valid_renders if
                          not len(glob.glob(J(v[1], '*.mp4')))
                          ]

    print("... found {} unfinished renders out of {} valid renders"
          .format(len(unfinished_renders), len(valid_renders)))

    print("Rendering videos: ")
    clean_render_dirs()

    # Render videos in multiprocessing queue
    multiprocessing.freeze_support()
    with multiprocessing.Pool(
            NUM_MINECRAFT_DIR, initializer=tqdm.tqdm.set_lock, initargs=(multiprocessing.RLock(),)) as pool:
        manager = ThreadManager(multiprocessing.Manager(), NUM_MINECRAFT_DIR, 0, 1)
        func = functools.partial(_render_videos, manager)
        num_rendered = list(
            tqdm.tqdm(pool.imap_unordered(func, unfinished_renders), total=len(unfinished_renders), desc='Files',
                      miniters=1,
                      position=0, maxinterval=1, smoothing=0))

    print('Rendered {} new files!'.format(sum(num_rendered)))


if __name__ == "__main__":
    main()
