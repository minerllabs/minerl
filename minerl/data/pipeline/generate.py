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
import math
import multiprocessing
from fractions import Fraction
from collections import OrderedDict
import os
import sys
import time
import numpy
import tqdm
import subprocess
import json
import traceback

#######################
### UTILITIES
#######################
from minerl.data.util import Blacklist
from minerl.data.util.constants import (
    J, E,
    EXP_MIN_LEN_TICKS,
    OUTPUT_DIR as WORKING_DIR,
    DATA_DIR,
    RENDER_DIR,
    BLACKLIST_TXT as BLACKLIST_PATH,
    ACTION_FILE,
    GOOD_MARKER_NAME, BAD_MARKER_NAME,
    METADATA_FILES,
    FAILED_COMMANDS,
    GENERATE_VERSION,
    touch,
    remove,
    ThreadManager
)

black_list = Blacklist()


def format_seconds(ticks):
    """
    Given ticks (int) returns a string of format hour:minutes:seconds
    """
    seconds = ticks / 20
    hours = int(seconds / 3600)
    seconds = seconds - hours * 3600
    minutes = int(seconds / 60)
    seconds = seconds - minutes * 60
    seconds = round(seconds, 3)
    return str(hours) + ':' + str(minutes) + ':' + str(seconds)


def add_key_frames(inputPath, segments):
    keyframes = []
    for segment in segments:
        # Convert ticks into video FPS (don't use render ms!)
        keyframes.append(format_seconds(segment[3]))
        keyframes.append(format_seconds(segment[4]))
    split_cmd = ['ffmpeg', '-i', J(inputPath, 'recording.mp4'),
                 '-c:a', 'copy',
                 '-c:v', 'copy',
                 '-force_key_frames',
                 ','.join(keyframes), J(inputPath, 'keyframes_recording.mp4')]
    # print('Running: ' + ' '.join(split_cmd))

    try:
        subprocess.check_output(split_cmd, stderr=subprocess.STDOUT)
    except Exception as e:
        print('COMMAND FAILED:', e)
        print(split_cmd)
        FAILED_COMMANDS.append(split_cmd)


def extract_subclip(input_path, start_tick, stop_tick, output_name):
    split_cmd = ['ffmpeg', '-ss', format_seconds(start_tick), '-i',
                 J(input_path, 'keyframes_recording.mp4'), '-t', format_seconds(stop_tick - start_tick),
                 '-vcodec', 'copy', '-acodec', 'copy', '-y', output_name]
    # print('Running: ' + ' '.join(split_cmd))
    try:
        subprocess.check_output(split_cmd, stderr=subprocess.STDOUT)
    except Exception as e:
        print('COMMAND FAILED:', e)
        print(split_cmd)
        FAILED_COMMANDS.append(split_cmd)


def parse_metadata(start_marker, stop_marker):
    try:
        metadata = {}
        startMeta = start_marker['value']['metadata']
        endMeta = stop_marker['value']['metadata']
        metadata['start_position'] = start_marker['value']['position']
        metadata['end_position'] = stop_marker['value']['position']
        metadata['start_tick'] = startMeta['tick'] if 'tick' in startMeta else None
        metadata['end_tick'] = endMeta['tick'] if 'tick' in endMeta else None
        metadata['start_time'] = start_marker['realTimestamp']
        metadata['end_time'] = stop_marker['realTimestamp']

        # Recording the string sent to us by Minecraft server including experiment specific data like if we won or not
        metadata['server_info_str'] = endMeta['expMetadata']
        metadata['server_metadata'] = json.loads(
            endMeta['expMetadata'][endMeta['expMetadata'].find('experimentMetadata') + 19:-1])

        # Not meaningful in some older streams but included for completeness
        metadata['server_info_str_start'] = startMeta['expMetadata']
        metadata['server_metadata_start'] = json.loads(
            startMeta['expMetadata'][startMeta['expMetadata'].find('experimentMetadata') + 19:-1])

        # Record if player was in the winners list
        if 'players' in metadata['server_metadata'] and 'winners' in metadata['server_metadata']:
            metadata['success'] = metadata['server_metadata']['players'][0] in metadata['server_metadata']['winners']

        return metadata
    except Exception as e:
        traceback.print_exc()
        raise e


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
        if filename not in black_list:
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
            # If it has been computed see if it is valid
            # or not.
            if E(J(render_path, GOOD_MARKER_NAME)):
                good_renders.append((recording_name, render_path))
            else:
                bad_renders.append((recording_name, render_path))
                black_list.add(recording_name)

    return good_renders, bad_renders


def _gen_sarsa_pairs(outputPath, manager, input, debug=False):
    n = manager.get_index()
    recordingName, inputPath = input
    ret = gen_sarsa_pairs(outputPath, inputPath, recordingName, lineNum=n, debug=debug)
    manager.free_index(n)
    return ret


def get_tick(ticks, ms):
    for i in range(len(ticks)):
        if ticks[i] >= ms:
            return i
    raise IndexError


# 3. generate sarsa pairs
def gen_sarsa_pairs(outputPath, inputPath, recordingName, lineNum=None, debug=False):
    # Script to to pair actions with video recording
    # All times are in ms and we assume a actions list, a timestamp file, and a dis-syncronous mp4 video

    # Decide if absolute or relative (old format)
    # Disable data generation for old format
    if E(J(inputPath, 'metaData.json')):
        metadata = json.load(open(J(inputPath, 'metaData.json')))
        if 'generator' in metadata:
            version = metadata['generator'].split('-')[-2]
            if int(version) < 103:
                return 0
    else:
        tqdm.tqdm.write('No metadata in ' + inputPath)
        return 0

    # Generate recording segments
    # Sorted pairs of (start, stop, exprementName) timestamps (in ms)
    segments = []
    numNewSegments = 0

    markers = OrderedDict()
    streamMetadata = json.load(open(J(inputPath, 'stream_meta_data.json')))

    if 'markers' in streamMetadata:
        markers_sp = streamMetadata['markers']
        for marker in markers_sp:
            markers[marker['realTimestamp']] = marker
    else:
        if debug:
            print('No markers found in stream_meta_data.json! Was it over-writen on re-render?')
        return 0

    startTime = None
    startTick = None
    startMarker = None

    # If we have to load univ_json ensure we don't load it again
    univ_json = None

    for key, marker in sorted(markers.items()):
        expName = ""
        # Get experiment name (its a malformed json so we have to look it up by hand)
        if 'value' in marker and 'metadata' in marker['value'] and 'expMetadata' in marker['value']['metadata']:
            meta = marker['value']['metadata']

            malformedStr = meta['expMetadata']
            jsonThing = json.loads(malformedStr[malformedStr.find('experimentMetadata') + 19:-1])
            if 'experiment_name' in jsonThing:
                expName = jsonThing['experiment_name']

                if expName == 'o_meat' and 'tick' in meta and 'stopRecording' in meta and meta['stopRecording']:
                    # Look backwards for meat at most 32 ticks in the past
                    # Lets players who were assigned obtain cooked X become winners for obtain cooked Y
                    tick = meta['tick']
                    if univ_json is None:
                        univ_json = json.loads(open(J(inputPath, 'univ.json')).read())
                    for i in range(32):
                        if str(tick - i) in univ_json and 'slots' in univ_json[str(tick - i)]:
                            slot = [elem.values() for elem in univ_json[str(tick - i)]['slots']['gui']['slots']
                                    if 'item.porkchopCooked' in elem.values()
                                    or 'item.beefCooked' in elem.values()
                                    or 'item.muttonCooked' in elem.values()]
                            if len(slot) == 0:
                                continue
                            if 'item.porkchopCooked' in slot[0]:
                                expName += '/cooked_pork'
                                break
                            if 'item.beefCooked' in slot[0]:
                                expName += '/cooked_beef'
                                break
                            if 'item.muttonCooked' in slot[0]:
                                expName += '/cooked_mutton'
                                break
                        else:
                            break
                if expName == 'o_bed' and 'tick' in meta and 'stopRecording' in meta and meta['stopRecording']:
                    # Look backwards for a bed at most 32 ticks in the past
                    # Lets players who were assigned obtain cooked X become winners for obtain cooked Y
                    tick = meta['tick']
                    if univ_json is None:
                        univ_json = json.loads(open(J(inputPath, 'univ.json')).read())
                    for i in range(32):
                        if str(tick - i) in univ_json and 'slots' in univ_json[str(tick - i)]:
                            slot = [elem.values() for elem in univ_json[str(tick - i)]['slots']['gui']['slots']
                                    if 'item.bed.black' in elem.values()
                                    or 'item.bed.white' in elem.values()
                                    or 'item.bed.yellow' in elem.values()]
                            if len(slot) == 0:
                                continue
                            if 'item.bed.black' in slot[0]:
                                expName += '/black'
                                break
                            if 'item.bed.yellow' in slot[0]:
                                expName += '/yellow'
                                break
                            if 'item.bed.white' in slot[0]:
                                expName += '/white'
                                break
                        else:
                            break

                def treechop_finished(tick):
                    gui = tick['slots']['gui']
                    num_logs = 0
                    if 'ContainerPlayer' in gui['type']:
                        for slot in gui['slots']:
                            # accounts for log and log2
                            if slot and 'log' in slot['name']:
                                num_logs += slot['count']
                    return num_logs >= 64

                def treechop_adjust(univ, t):
                    return

                def o_iron_finished(tick):
                    try:
                        changes = tick['diff']['changes']
                        for change in changes:
                            if change['item'] == 'minecraft:iron_pickaxe' and change['quantity_change'] > 0:
                                return True
                    except KeyError:
                        pass
                    return False

                def o_iron_adjust(univ, t):
                    try:
                        univ[t]['diff']['changes'] = [{
                            'item': 'minecraft:iron_pickaxe', 'variant': 0, 'quantity_change': 1}]
                    except KeyError:
                        pass

                def o_dia_finished(tick):
                    try:
                        changes = tick['diff']['changes']
                        for change in changes:
                            if change['item'] == 'minecraft:diamond' and change['quantity_change'] > 0:
                                return True
                    except KeyError:
                        pass
                    return False

                def o_dia_adjust(univ, t):
                    # print(univ[t])
                    try:
                        univ[t]['diff']['changes'] = [{
                            'item': 'minecraft:diamond', 'variant': 0, 'quantity_change': 1}]
                        # print(univ[t])
                    except KeyError:
                        pass

                def nav_finished(tick):
                    try:
                        for block in tick['touched_blocks']:
                            if 'minecraft:diamond_block' in block['name']:
                                return True
                    except KeyError:
                        pass
                    return False

                def nav_adjust(univ, t):
                    try:
                        univ[t]['navigateHelper'] = 'minecraft:diamond_block'
                    except KeyError:
                        pass

                finish_conditions = {
                    'survivaltreechop': (treechop_finished, treechop_adjust),
                    'o_iron': (o_iron_finished, o_iron_adjust),
                    'o_dia': (o_dia_finished, o_dia_adjust),
                    'navigate': (nav_finished, nav_adjust),
                    'navigateextreme': (nav_finished, nav_adjust)
                }

                for finish_expName in finish_conditions:
                    condition, adjust = finish_conditions[finish_expName]
                    if expName == finish_expName and 'tick' in meta and 'stopRecording' in meta and meta[
                        'stopRecording'] and startTick is not None:
                        if univ_json is None:
                            univ_json = json.loads(open(J(inputPath, 'univ.json')).read())

                        cond_satisfied = []
                        metadata = parse_metadata(startMarker, marker)
                        # print("Here is the metadata:")
                        # print(metadata)
                        # print("there it was")

                        # TODO these should be quit handlers that return success True/False
                        for i in range(min(400, meta['tick'] - startTick)):
                            considered_tick = (meta['tick'] - i)
                            try:
                                if condition(univ_json[str(considered_tick)]):
                                    cond_satisfied.append(considered_tick)
                            except KeyError:
                                pass

                        cond_satisfied = sorted(cond_satisfied)

                        if cond_satisfied:
                            meta['tick'] = cond_satisfied[0]
                        else:
                            # Add change if winner
                            try:
                                if len(metadata['server_metadata']['winners']) > 0:
                                    adjust(univ_json, str(meta['tick']))
                            except (KeyError, TypeError) as e:
                                traceback.print_exc()

            else:
                continue

        if 'startRecording' in meta and meta['startRecording'] and 'tick' in meta:
            # If we encounter a start marker after a start marker there is an error and we should throw away this
            # previous start marker and start fresh
            startTime = key
            startTick = meta['tick']
            startMarker = marker

        if 'stopRecording' in meta and meta['stopRecording'] and startTime is not None:
            segments.append((startMarker, marker, expName, startTick, meta['tick']))
            # segments.append((startTime, key, expName, startTick, meta['tick'], startMarker, marker))
            startTime = None
            startTick = None

    # Layout of segments (new)
    # 0.             1.            2.                3.           4.
    # Start Marker : Stop Marker : Experiment Name : Start Tick : Stop Tick

    # (hack patch)
    # 0.          1.         2.        3.          4.         5.             6
    # startTime : stopTime : expName : startTick : stopTick : startMarker :  stopMarker

    if not E(J(inputPath, "recording.mp4")):
        if debug:
            tqdm.tqdm.write('No recording found in ' + inputPath)
        return 0

    if len(markers) == 0:
        if debug:
            tqdm.tqdm.write('No valid markers found')
        return 0

    if univ_json is None:
        univ_json = json.loads(open(J(inputPath, 'univ.json')).read())

    if 'ticks' not in univ_json:
        if debug:
            tqdm.tqdm.write('No ticks file in ' + inputPath)
        return 0

    ticks = univ_json['ticks']
    videoOffset_ms = streamMetadata['start_timestamp']
    videoOffset_ticks = get_tick(ticks, videoOffset_ms)

    segments = [(segment[0],
                 segment[1],
                 segment[2],
                 segment[3] - videoOffset_ticks,
                 segment[4] - videoOffset_ticks)
                for segment in segments]
    segments = [segment for segment in segments if segment[4] - segment[3] > EXP_MIN_LEN_TICKS and segment[3] > 0]

    pbar = tqdm.tqdm(total=len(segments), desc='Segments', leave=False, position=lineNum)

    if not segments or len(segments) == 0:
        if debug:
            tqdm.tqdm.write('No segments in ' + inputPath)
        return 0
    try:
        if E(J(inputPath, 'keyframes_recording.mp4')):
            os.remove(J(inputPath, 'keyframes_recording.mp4'))
        add_key_frames(inputPath, segments)
    except subprocess.CalledProcessError as exception:
        open('errors.txt', 'a+').write(
            "Error splitting {}:\033[0;31;47m {}        \033[0m 0;31;47m".format(recordingName,
                                                                                 exception) + inputPath + '\n')
        return 0

    for pair in segments:
        time.sleep(0.05)
        startMarker = pair[0]
        stopMarker = pair[1]
        experimentName = pair[2]
        startTick = pair[3]
        stopTick = pair[4]

        # BAH introduce versioning
        experiment_id = 'g{}_{}'.format(GENERATE_VERSION, recordingName[len('player_stream_'):]) + "_" + str(
            int(startTick)) + '-' + str(int(stopTick))
        output_name = J(outputPath, experimentName, experiment_id, 'recording.mp4')
        univ_output_name = J(outputPath, experimentName, experiment_id, 'univ.json')
        meta_output_name = J(outputPath, experimentName, experiment_id, 'metadata.json')
        output_dir = os.path.dirname(output_name)
        if not E(output_dir):
            os.makedirs(output_dir)
        if not (E(output_name) and E(univ_output_name) and E(meta_output_name)):
            try:
                # Only load universal json if needed
                if univ_json is None:
                    univ_json = json.loads(open(J(inputPath, 'univ.json')).read())

                # Remove potentially stale elements
                if E(output_name): os.remove(output_name)
                if E(univ_output_name): os.remove(univ_output_name)
                if E(meta_output_name): os.remove(meta_output_name)

                json_to_write = {}
                for idx in range(startTick, stopTick + 1):
                    json_to_write[str(idx - startTick)] = univ_json[str(idx)]

                # Split universal.json
                json.dump(json_to_write, open(univ_output_name, 'w'))

                # Split metadata.json
                json.dump(metadata, open(meta_output_name, 'w'))

                # Split video (without re-encoding)
                extract_subclip(inputPath, startTick, stopTick, output_name)

                numNewSegments += 1
                pbar.update(1)

            except KeyboardInterrupt:
                return numNewSegments
            except KeyError:
                open('errors.txt', 'a+').write(
                    "Key Error " + str(idx) + " not found in universal json: " + inputPath + '\n')
                continue
            except Exception as e:
                open('errors.txt', 'a+').write(
                    "Exception in segment rendering" + str(e) + str(type(e)) + inputPath + '\n')
                continue
    return numNewSegments


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
    numSegments = []
    if E('errors.txt'):
        os.remove('errors.txt')
    try:
        numW = int(sys.argv[1]) if len(sys.argv) > 1 else 2

        multiprocessing.freeze_support()
        with multiprocessing.Pool(numW, initializer=tqdm.tqdm.set_lock, initargs=(multiprocessing.RLock(),)) as pool:
            manager = ThreadManager(multiprocessing.Manager(), numW, 1, 1)
            func = functools.partial(_gen_sarsa_pairs, DATA_DIR, manager)
            numSegments = list(
                tqdm.tqdm(pool.imap_unordered(func, valid_renders), total=len(valid_renders), desc='Files', miniters=1,
                          position=0, maxinterval=1))

            # for recording_name, render_path in tqdm.tqdm(valid_renders, desc='Files'):
            #     numSegmentsRendered += gen_sarsa_pairs(render_path, recording_name, DATA_DIR)
    except Exception as e:
        print('\n' * numW)
        print("Exception in pool: ", type(e), e)
        print('Rendered {} new segments in total!'.format(sum(numSegments)))
        if E('errors.txt'):
            print('Errors:')
            print(open('errors.txt', 'r').read())
        return

    numSegmentsRendered = sum(numSegments)

    print('\n' * numW)
    print('Rendered {} new segments in total!'.format(numSegmentsRendered))
    if E('errors.txt'):
        print('Errors:')
        print(open('errors.txt', 'r').read())


if __name__ == "__main__":
    main()
