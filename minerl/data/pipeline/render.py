#!/usr/bin/python3.5
"""
render.py
# This script renders the merged experiments into
# actions and videos by doing the following
# 1) Unzipping various mcprs and building render directories
#    containing meta data.
# 2) Running the action_rendering scripts
# 3) Running the video_rendering scripts

Inputs: MCPR files from merge.py script.
Outputs:
    * Unedited MP4 files for entire player stream, including lobby video and
        several episodes in the same MP4 file (generate.py will slice out individual
        episodes later).
    * univ.json and metadata.json
        * univ.json contains a plethora of information including equip swaps, item pickups,
            "touched block" events, etc which is later processed into Numpy actions and
            observations. Again, this is unsliced at this stage.
        * metadata.json: ReplayMod metadata, doesn't seem important.
        * markers.json: Contains stop- and start-recording timesteps used to slice
            player streams into individual episodes.


By default, this generates low-res videos of dimensions 64x64.
To generate videos of a different resolution, set or `export` the
MINERL_RENDER_WIDTH and MINERL_RENDER_HEIGHT environment variables.
(e.g.: `export MINERL_RENDER_WIDTH=1920 MINERL_RENDER_HEIGHT=1080`).
"""
from datetime import datetime, timezone, timedelta
import functools
import re
import json
import os
from pathlib import Path
import psutil
import shutil
from shutil import copyfile
import time
import traceback
from typing import Callable, Container, List, Optional, TextIO, Tuple, Union
import subprocess
import sys
import glob
import zipfile

import numpy as np
import tqdm

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
    X11_ERROR_DIR,
    RENDER_TIMEOUT_ERROR_DIR,
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


def construct_render_dirs() -> None:
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
            X11_ERROR_DIR,
            RENDER_TIMEOUT_ERROR_DIR,
            ]

    for dir in dirs:
        if not E(dir):
            os.makedirs(dir)


def select_demonstrations(
        blacklist: Container[str],
        regex_pattern: Optional[str] = None,
) -> List[Tuple[str, str]]:
    # We only care about unrendered directories.
    render_dirs = []

    for filename in tqdm.tqdm(os.listdir(MERGED_DIR)):
        if filename.endswith(".mcpr") and filename not in blacklist:
            recording_name = filename.split(".mcpr")[0]
            render_path = J(RENDER_DIR, recording_name)

            render_dirs.append((recording_name, render_path))

    print(f"Found {len(render_dirs)} .mcpr files.")

    # TODO(shwang): Stop returning a Tuple[str, str] here and elsewhere.
    #   Instead, use a single pathlib.Path, and use path.name to get the
    #   "recording_name".
    if regex_pattern is None:
        result = render_dirs
    else:
        regex = re.compile(regex_pattern)
        filtered_dirs = []
        for recording_name, render_path in render_dirs:
            if regex.search(recording_name):
                filtered_dirs.append((recording_name, render_path))
        print(f"Kept {len(filtered_dirs)} directories after applying regex '{regex_pattern}'.")
        result = filtered_dirs

    for _, render_path in result:
        if not E(render_path):
            os.makedirs(render_path)

    return result


# 2. render metadata from the files.
def render_metadata(renders: List[Tuple[str, str]]):
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
                        return recording.extract(fname, render_path)

                    # If everything is good extract the metadata.
                    for mfile in METADATA_FILES:
                        assert str(mfile) in [str(x) for x in recording.namelist()]
                        if not E(J(render_path, mfile)):
                            extract(mfile)

                    # check that stream_meta_data is good
                    with open(J(render_path, 'metaData.json'), 'r') as f:
                        # print(render_path)
                        jbos = json.load(f)
                        # BAH TODO duration seems to be broken
                        # assert (jobs["duration"] > 60000 or jbos["duration"] == 0)

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

                python_exec_path = sys.executable or "python3"
                p = subprocess.Popen(
                    [python_exec_path, "parse_action.py", os.path.abspath(action_mcbr)],
                    cwd='action_rendering',
                )
                returncode = (p.wait())
                assert returncode == 0

                good_renders.append((recording_name, render_path))
            except AssertionError:
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


def _get_most_recent_file(
        parent_dir: Union[str, Path],
        suffix: str = "",
        min_mtime: Optional[float] = None,
        debug_file_desc: Optional[str] = None,
) -> Optional[Path]:
    """Returns a Path to most recently modified file in the parent directory, or
    None if no such file exists.

    Args:
        parent_dir: The Path is returned for a file inside this directory.
        suffix: Files whose names don't end with this string are skipped.
        min_mtime: Optional timestamp (in seconds since Unix epoch).
            If all files have mtime less than this argument, then return None.
        debug_file_desc: If provided, then print debug logs when None is returned
            due to `min_mtime`.
    """
    parent_dir = Path(parent_dir)
    paths = list(parent_dir.glob(f"*{suffix}"))
    if len(paths) == 0:
        return None
    else:
        result = max(paths, key=os.path.getmtime)
        if min_mtime is not None and os.path.getmtime(result) < min_mtime:
            if debug_file_desc is not None:
                print(f"\tError! {debug_file_desc} is older than replay!")
                print(f"\tskipping due to out-of-date {debug_file_desc}.")
            return None
        else:
            return result


def _get_error_dir(log_line: str, debug=False) -> Optional[str]:
    if re.search(r"EOFException:", log_line):
        if debug:
            print("\tfound java.io.EOFException")
        return EOF_EXCEP_DIR
    elif re.search(r"Adding time keyframe at \d+ time -\d+", log_line):
        if debug:
            print("\tfound 0 length file")
        return ZEROLEN_DIR
    elif re.search(r"NullPointerException", log_line):
        if not re.search(r'exceptionCaught', log_line):
            if debug:
                print("\tNullPointerException")
            return NULL_PTR_EXCEP_DIR
    elif re.search(r"zip error", log_line) or re.search(r"zip file close", log_line):
        if debug:
            print('ZIP file error')
        return ZIP_ERROR_DIR
    elif re.search(r'connect to X11 window server', log_line):
        if debug:
            print("X11 error")
        return X11_ERROR_DIR
    elif re.search(r'Xvfb failed to start', log_line):
        if debug:
            print("X11 error -- `apt install x11vnc`?")
        return X11_ERROR_DIR
    elif re.search(r'no lwjgl64 in java', log_line):
        if debug:
            print("missing lwjgl.")
        return OTHER_ERROR_DIR
    else:
        return None

    # elif re.search(r"Exception", logLine):
    #   if debug:
    #       print("Unknown exception!!!")
    #   error_dir = OTHER_ERROR_DIR


def _nonblocking_readlines(nonblocking_file_handler: TextIO) -> List[str]:
    """
    A non-blocking function that returns new lines in a file since the last call.

    Args:
        nonblocking_file_handler: A file handler opened with the `os.O_NONBLOCK` option.
    """
    results = []
    while True:
        line = nonblocking_file_handler.readline()
        if len(line) > 0:
            results.append(line)
        else:
            break
    return results


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

    if not os.path.isdir(MINECRAFT_DIR[index]):
        raise RuntimeError(f"{MINECRAFT_DIR[index]} doesn't exist")

    # Ensure that recording_path exists.
    os.makedirs(RECORDING_PATH[index], exist_ok=True)

    # Clear recording directory to protect against crash messages
    for messyFile in glob.glob(J(RECORDING_PATH[index], '*')):
        try:
            os.remove(messyFile)
        except IsADirectoryError:
            shutil.rmtree(messyFile)

    p: subprocess.Popen = None
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
        notFound = True
        NO_RENDER_UPDATE_TIMEOUT = timedelta(minutes=10)
        timeout_datetime: datetime = datetime.now(tz=timezone.utc) + NO_RENDER_UPDATE_TIMEOUT

        while notFound:
            if os.path.exists(FINISHED_FILE[index]) or p.poll() is not None:
                if os.path.exists(FINISHED_FILE[index]):
                    os.remove(FINISHED_FILE[index])
                    notFound = False
                    numSuccessfulRenders += 1

                try:
                    if debug:
                        print("Waiting for Minecraft to close")
                    p.wait(400)
                    if debug:
                        print("Minecraft closed")
                except TimeoutError:
                    tqdm.tqdm.write("Minecraft close Timeout")
                    killMC(p)
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
                log_lines = _nonblocking_readlines(logFile)
                for log_line in log_lines:
                    lineCounter += 1
                    error_dir = _get_error_dir(log_line)
                    if error_dir:
                        if debug:
                            print("\tline {}: {}".format(lineCounter, log_line))
                        print(error_dir)
                        logError(error_dir, recording_name, skip_path, index)
                        break

                artifact_paths = [
                    _get_most_recent_file(RENDERED_VIDEO_PATH[index], ".mp4"),
                    _get_most_recent_file(RENDERED_LOG_PATH[index], ".json"),
                    _get_most_recent_file(RENDERED_VIDEO_PATH[index], ".json"),
                ]
                artifact_paths = [x for x in artifact_paths if x is not None]

                if len(artifact_paths) > 0:
                    # mtime is when the contents of the file was most recently updated,
                    # stored as a UTC timestamp.
                    # We first convert this timestamp to `datetime` for easy comparison.
                    artifact_mtimes = [os.path.getmtime(path) for path in artifact_paths]
                    most_recent_mtime = max(artifact_mtimes)
                    most_recent_datetime = datetime.fromtimestamp(
                        most_recent_mtime, tz=timezone.utc)
                    possible_new_timeout = most_recent_datetime + NO_RENDER_UPDATE_TIMEOUT

                    # Extend timeout if an artifact file was updated recently.
                    # Under normal run conditions, this extension fires off almost every time.
                    if possible_new_timeout > timeout_datetime:
                        timeout_datetime = possible_new_timeout

                # Timeout if no artifact files have been created or modified within
                # the last `NO_RENDER_UPDATE_TIMEOUT` amount of time.
                if datetime.now(tz=timezone.utc) > timeout_datetime:
                    tqdm.tqdm.write(
                        f"Rendering timed out ({NO_RENDER_UPDATE_TIMEOUT} "
                        "time without artifact write)"
                    )
                    logError(RENDER_TIMEOUT_ERROR_DIR, recording_name, skip_path, index)
                    break

                time.sleep(1)  # Sleep to limit unnecessary polling.

        time.sleep(1)
        logFile.close()
        if notFound:
            remove(J(RECORDING_PATH[index], (recording_name + ".mcpr")))
            return 0
        else:
            print("file found!")

        # GET RECORDING
        video_path = _get_most_recent_file(
            RENDERED_VIDEO_PATH[index], ".mp4", copy_time, "rendered video")

        # GET UNIVERSAL ACTION FORMAT
        log_path = _get_most_recent_file(
            RENDERED_LOG_PATH[index], ".json", copy_time, "action/univ json")

        # GET new markers.json
        marker_path = _get_most_recent_file(
            RENDERED_VIDEO_PATH[index], ".json", copy_time, "markers.json")

        if video_path and log_path and marker_path:
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

            metadata['start_timestamp'] = int(video_path.name.split('_')[1])
            metadata['stop_timestamp'] = int(
                video_path.name.split('_')[2].split('-')[0])
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
            remove(J(RECORDING_PATH[index], (recording_name + ".mcpr")))
            return 0

        # Remove mcpr file from dir
        remove(J(RECORDING_PATH[index], (recording_name + ".mcpr")))
    finally:
        if p is not None:
            # Didn't finish
            try:
                p.wait(4)  # 4 seconds
            except (TimeoutError, subprocess.TimeoutExpired):
                killMC(p)
            time.sleep(10)
    return 1


def clean_render_dirs():
    paths_to_clear = []

    for dir_list in [RENDERED_VIDEO_PATH, RECORDING_PATH, RENDERED_LOG_PATH]:
        for d in dir_list:
            paths_to_clear.extend(glob.glob(J(d, '*')))

    paths_to_clear.extend(LOG_FILE)
    paths_to_clear.extend(FINISHED_FILE)

    for path in paths_to_clear:
        remove(path)


def main(n_workers=NUM_MINECRAFT_DIR, parallel=True, regex_pattern=None):
    """
    The main render script.
    """
    # 1. Load the blacklist.
    blacklist = set(np.loadtxt(BLACKLIST_PATH, dtype=np.str).tolist())

    print("Constructing render directories.")
    construct_render_dirs()
    renders = select_demonstrations(blacklist, regex_pattern)

    if len(renders) == 0:
        print("No render jobs selected. Aborting.")
        exit(1)

    print("Validating metadata from files:")
    valid_renders, invalid_renders = render_metadata(renders)
    print(len(valid_renders))
    # print("Rendering actions: ")
    # valid_renders, invalid_renders = render_actions(valid_renders)
    print("... found {} valid recordings out of {} selected demonstrations".format(
        len(valid_renders), len(renders)))

    unfinished_renders = [v for v in valid_renders if
                          not len(glob.glob(J(v[1], '*.mp4')))
                          ]

    print("... found {} unfinished renders out of {} valid renders"
          .format(len(unfinished_renders), len(valid_renders)))

    print("Rendering videos: ")
    clean_render_dirs()

    if parallel:
        import multiprocessing
    else:
        import multiprocessing.dummy as multiprocessing

    # Render videos in multiprocessing queue
    multiprocessing.freeze_support()
    with multiprocessing.Pool(
            n_workers, initializer=tqdm.tqdm.set_lock, initargs=(multiprocessing.RLock(),)) as pool:
        manager = ThreadManager(multiprocessing.Manager(), NUM_MINECRAFT_DIR, 0, 1)
        func = functools.partial(_render_videos, manager)
        num_rendered = list(
            tqdm.tqdm(pool.imap_unordered(func, unfinished_renders), total=len(unfinished_renders), desc='Files',
                      miniters=1,
                      position=0, maxinterval=1, smoothing=0))

    print('Rendered {} new files!'.format(sum(num_rendered)))


if __name__ == "__main__":
    main()
