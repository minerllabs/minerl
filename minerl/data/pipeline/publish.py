# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

"""
This script generates the actual datasets that are loaded by MineRL.

The publish function uses the Handlers associated with every registered
EnvSpec to generate an numpy file containing all the formatted observations and
actions (these are processed from a file called univ.json), and places the
video file and this numpy file in the same directory.

The package function generates the .tar files that should be uploaded to
s3://minerl/.
"""
import logging
import functools
import hashlib
import os
import random
import re
import sys
from typing import List, Optional, Tuple

import cv2
import tqdm
import shutil
import numpy as np
import json
import signal
import tarfile

import minerl.herobraine.envs as envs
import minerl.herobraine.hero.handlers as handlers
from minerl.data.util import Blacklist

import minerl

PUBLISHER_VERSION = minerl.data.DATA_VERSION

#######################
#      UTILITIES      #
#######################
from minerl.data.util.constants import (
    ACTIONABLE_KEY, HANDLER_TYPE_SEPERATOR, J, E, MONITOR_KEY, OBSERVABLE_KEY, REWARD_KEY,
    touch,
    remove,
    METADATA_FILES,
    ACTION_FILE,
    BAD_MARKER_NAME,
    GOOD_MARKER_NAME,
    ACTION_FILE,
    DATA_DIR,
    ThreadManager
)
from minerl.herobraine.hero import spaces
import collections
from minerl.herobraine.wrapper import EnvWrapper
from collections import OrderedDict
from minerl.herobraine.wrappers.obfuscation_wrapper import Obfuscated

FAILED_COMMANDS = []


def flatten(d, parent_key='', sep='$'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def read_frame(cap):
    try:
        ret, frame = cap.read()
        if ret:
            cv2.cvtColor(frame, code=cv2.COLOR_BGR2RGB, dst=frame)
            frame = np.asarray(np.clip(frame, 0, 255), dtype=np.uint8)

        return ret, frame
    except Exception as err:
        raise err


def calculate_frame_count(video_path):
    ret, frame_num = True, 0
    cap = cv2.VideoCapture(video_path)
    while ret:
        ret, _ = read_frame(cap)
        if ret:
            frame_num += 1
    # TODO modify recording to have the correct video metadata (for external loading)
    # cap.set number of frames (frame_number)
    return frame_num


##################
#    PIPELINE    #
##################

def remove_initial_frames(universal):
    """
    Removes the intial frames of an episode.
    """
    # Detect teleportation frames
    # Check for a pressure_plate starting the experiment
    touched_pressure_plate, start_tick, skip_next_n = False, None, 0
    for tick, obs in universal.items():
        # If we see more than 5 ticks of consecutive air
        # if len(universal["0"]['touched_blocks']) == 0 \
        #         and len(universal["1"]['touched_blocks']) == 0 \
        #         and len(universal["2"]['touched_blocks']) == 0 \
        #         and len(universal["3"]['touched_blocks']) == 0 \
        #         and len(universal["4"]['touched_blocks']) == 0:
        #     break
        # Determine the first time we are touching a stone pressure plate
        if skip_next_n > 0:
            skip_next_n -= 1
            pass
        elif any([block['name'] == 'minecraft:stone_pressure_plate' for block in obs['touched_blocks']]):
            # print('\nTouched pressure plate {}'.format(tick))
            touched_pressure_plate = True
            skip_next_n = 5
        # If we have touched a pressure plate skip until we touch the next non air nor water block
        elif touched_pressure_plate and len(obs['touched_blocks']) > 0 and \
                (obs['touched_blocks'][0]['name'] != 'minecraft:water' or len(obs['touched_blocks']) > 1):
            # print('\nPressure-plate to ground at {}'.format(tick))
            start_tick = tick
            break
        pass

    # Truncate the beginning of the episode (we align videos and universals by the end)
    if start_tick is None:
        # If we could not find a pressure_plate we may have started in the air - skip till we are on the ground
        on_ground_for = 0
        for tick, obs in universal.items():
            # TODO test if we can start once we are not touching water at all
            if len(obs['touched_blocks']) > 0 and \
                    (obs['touched_blocks'][0]['name'] != 'minecraft:water' or len(obs['touched_blocks']) > 1):
                on_ground_for += 1
                if on_ground_for >= 8:
                    start_tick = tick
                    # print('\nGround for a while at {} loc {}'.format(tick, obs))
                    break
            else:
                on_ground_for = 0
    if start_tick is None:
        # If not on the ground for at least 5 how about 1
        for tick, obs in universal.items():
            if len(obs['touched_blocks']) != 0:
                start_tick = tick
                break
    # Remove teleportation frames
    if start_tick is None:
        # We don't have a valid video
        return 0
    for i in range(int(start_tick)):
        universal.pop(str(i), None)

    # Then remove all high speed travel
    prev_pos = None
    for tick, obs in universal.items():
        p = obs['compass']['position']
        pos = np.array([p['x'], p['y'], p['z']])
        if prev_pos is None:
            prev_pos = pos
            continue
        elif np.linalg.norm(pos - prev_pos) < (4.3 / 20) and len(obs['custom_action']['actions']) > 0:
            start_tick = tick
            # print('\nslowed down to {} at {}'.format(
            #     math.sqrt(sum([(new - old)**2 for new, old in zip(pos, prev_pos)])), tick))
            break
        elif np.linalg.norm(pos - prev_pos) < (0.001 / 20):
            start_tick = tick
            # print('\nstopped at {}'.format(tick))
            break
        prev_pos = pos

    # Remove high speed travel frames
    for i in range(int(start_tick)):
        # print("popping")
        universal.pop(str(i), None)

    # Then remove all no-ops after we touch the ground
    for tick, obs in universal.items():
        if len(obs['custom_action']['actions']) != 0:
            start_tick = tick
            # tqdm.tqdm.write('started moving at {}'.format(tick))
            break

    # Remove no-op frames
    for i in range(int(start_tick)):
        universal.pop(str(i), None)

    return universal


# 1. Construct data working dirs.
def construct_data_dirs(black_list, regex_pattern: Optional[str] = None) -> List[Tuple[str, str]]:
    """
    Constructs the render directories omitting
    elements on a blacklist.
    """
    print(DATA_DIR)
    if not E(DATA_DIR):
        os.makedirs(DATA_DIR)

    data_dirs = []
    for exp_folder in tqdm.tqdm(next(os.walk(DATA_DIR))[1], desc='Directories', position=0):
        for experiment_dir in tqdm.tqdm(next(os.walk(J(DATA_DIR, exp_folder)))[1], desc='Experiments', position=1):
            if not exp_folder.startswith('MineRL') \
                    and experiment_dir.split('g1_')[-1] not in black_list:
                data_dirs.append((experiment_dir, exp_folder))

    print(f"Found {len(data_dirs)} publish jobs.")

    if regex_pattern is None:
        return data_dirs
    else:
        filtered_dir = []
        regex = re.compile(regex_pattern)

        for experiment_dir, exp_folder in data_dirs:
            if regex.search(experiment_dir) or regex.search(exp_folder):
                filtered_dir.append((experiment_dir, exp_folder))
        print(
            f"Kept {len(filtered_dir)} publish jobs after filtering with regex '{regex_pattern}'.")
        return filtered_dir


def _render_data(output_root, manager, input_tuple, parallel: bool = True):
    if parallel:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    n = manager.get_index()
    recording_dir, experiment_folder = input_tuple
    black_list = Blacklist()
    ret = render_data(output_root, recording_dir, experiment_folder, black_list, lineNum=n)
    manager.free_index(n)
    return ret


# 2. render numpy format
def render_data(output_root, recording_dir, experiment_folder, black_list, lineNum=None):
    # Script to to pair actions with video recording
    # All times are in ms and we assume a actions list, a timestamp file, and a dis-synchronous mp4 video

    # File-Names
    segment_str = recording_dir.split('g1_')[-1]
    if segment_str in black_list:
        return 0

    # Generate Numpy
    source_folder = J(DATA_DIR, experiment_folder, recording_dir)
    recording_source = J(source_folder, 'recording.mp4')
    universal_source = J(source_folder, 'univ.json')
    metadata_source = J(source_folder, 'metadata.json')

    # Gather all renderable environments for this experiment directory
    rendered_envs = 0
    filtered_environments = [
        env_spec for env_spec in envs.ENV_SPECS if env_spec.is_from_folder(experiment_folder)]
    # Don't render if files are missing
    if not E(source_folder) or not E(recording_source) or not E(universal_source) or not E(metadata_source):
        black_list.add(segment_str)
        return 0

    # Process universal json
    with open(universal_source, 'r') as json_file:
        universal = json.load(json_file)

        universal = remove_initial_frames(universal)

        for env_spec in filtered_environments:
            dest_folder = J(output_root, env_spec.name, 'v{}_{}'
                            .format(PUBLISHER_VERSION, segment_str))
            recording_dest = J(dest_folder, 'recording.mp4')
            rendered_dest = J(dest_folder, 'rendered.npz')
            metadata_dest = J(dest_folder, 'metadata.json')

            # TODO remove to incrementally render files - during testing re-render each time
            if E(J(dest_folder, 'rendered.npz')):
                os.remove(J(dest_folder, 'rendered.npz'))

            # Don't render again, ensure source exits
            if E(rendered_dest):
                continue

            env_spec.reset()

            # Load relevant handlers
            info_handlers = [obs for obs in env_spec.observables
                             if not isinstance(obs, handlers.POVObservation)]
            reward_handlers = env_spec.rewardables
            # TODO (R): Support done handlers.
            # done_handlers = [hdl for hdl in task.create_mission_handlers() if isinstance(hdl, handlers.QuitHandler)]
            action_handlers = env_spec.actionables
            monitor_handlers = env_spec.monitors

            all_handlers = [hdl for sublist in [info_handlers, reward_handlers, action_handlers] for hdl in sublist]

            try:

                published = {
                    REWARD_KEY: np.array(
                        [sum([hdl.from_universal(universal[tick]) for hdl in reward_handlers]) for tick in universal],
                        dtype=np.float32)[1:]
                }

                for tick in universal:
                    tick_data = {}
                    for _prefix, hdlrs in [
                        (OBSERVABLE_KEY, info_handlers),
                        (ACTIONABLE_KEY, action_handlers),
                        (MONITOR_KEY, monitor_handlers),
                    ]:
                        if _prefix not in tick_data:
                            tick_data[_prefix] = OrderedDict()

                        for handler in hdlrs:
                            # Apply the handler from_universal to the universal[tick]
                            try:
                                val = handler.from_universal(universal[tick])
                            except KeyError:
                                import traceback
                                traceback.print_exc()
                                print("KeyError:", recording_dir, environment.name)
                                raise
                            assert val in handler.space, \
                                "{} is not in {} for handler {}".format(val, handler.space, handler.to_string)
                            tick_data[_prefix][handler.to_string()] = val

                        # Perhaps we can wrap here
                        if isinstance(env_spec, EnvWrapper):
                            if _prefix == OBSERVABLE_KEY:
                                tick_data[_prefix]['pov'] = (
                                    env_spec.observation_space['pov'].no_op())
                                tick_data[_prefix] = env_spec.wrap_observation(tick_data[_prefix])
                                del tick_data[_prefix]['pov']
                            elif _prefix == ACTIONABLE_KEY:
                                tick_data[_prefix] = env_spec.wrap_action(tick_data[_prefix])

                    tick_data = flatten(tick_data, sep=HANDLER_TYPE_SEPERATOR)
                    for k, v in tick_data.items():
                        try:
                            published[k].append(v)
                        except KeyError:
                            published[k] = [v]

                # Adjust the action one forward (recall that the action packet is one off.)
                for k in published:
                    if k.startswith(ACTIONABLE_KEY):
                        published[k] = published[k][1:]

            except NotImplementedError as err:
                print('Exception:', str(err), 'found with environment:', env_spec.name)
                raise err
            except KeyError as err:
                print("Key error in file - check from_universal for handlers")
                print(err)
                continue
            except AssertionError as e:
                # Warn the user if some of the observatiosn or actions don't fall in the gym.space 
                # (The space checking assertion error from above was raised)
                print("Warning!" + str(e))
                import traceback
                traceback.print_exc()
                continue
            except Exception as e:
                print("caught exception:", str(e))
                for hdl in all_handlers:
                    try:
                        for tick in universal:
                            hdl.from_universal(universal[tick])
                    except Exception as f:
                        print("Exception <", str(f), "> for command handler:", hdl)
                        continue
                raise e

            reason = env_spec.get_blacklist_reason(published)
            if reason is not None:
                assert len(reason) > 0, "reason needs to be non-empty str or None"
                print(f"Blacklisting {env_spec.name} demonstration {segment_str} "
                      f"because: '{reason}'."
                      )
                black_list.add(segment_str)
                return 0

            # Setup destination root
            if not E(dest_folder):
                try:
                    os.makedirs(dest_folder, exist_ok=True)
                except OSError as exc:
                    print('Could not make folder: ', dest_folder)
                    raise exc

            # Render metadata
            try:
                # Copy video if necessary
                if not E(recording_dest):
                    shutil.copyfile(src=recording_source, dst=recording_dest)
                np.savez_compressed(rendered_dest, **published)

                with open(metadata_source, 'r') as meta_file:
                    source = json.load(meta_file)
                    metadata_out = {}
                    metadata_out['success'] = bool(
                        env_spec.determine_success_from_rewards(published['reward']))
                    metadata_out['duration_ms'] = len(
                        published['reward']) * 50  # source['end_time'] - source['start_time']
                    metadata_out['duration_steps'] = len(published['reward'])
                    metadata_out['total_reward'] = sum(published['reward'])
                    metadata_out['stream_name'] = 'v{}{}'.format(
                        PUBLISHER_VERSION, recording_dir[len('g1'):])
                    metadata_out['true_video_frame_count'] = calculate_frame_count(recording_dest)
                    with open(metadata_dest, 'w') as meta_file_out:
                        json.dump(metadata_out, meta_file_out)

                rendered_envs += 1
            except (KeyError, ValueError) as e:
                print(e)
                shutil.rmtree(dest_folder, ignore_errors=True)
                continue

    return rendered_envs


def publish(n_workers=56, parallel=True, regex_pattern: Optional[str] = None):
    """
    The main render script.
    """
    black_list = Blacklist()
    valid_data = construct_data_dirs(black_list, regex_pattern)
    print(valid_data)

    print("Publishing segments: ")
    num_segments = []
    if E('errors.txt'):
        os.remove('errors.txt')
    try:
        if parallel:
            import multiprocessing
            multiprocessing.freeze_support()
        else:
            # Fake multiprocessing -- uses threads instead of processes for
            # easier debugging and PDB-compatibility.
            import multiprocessing.dummy as multiprocessing

        multiprocessing.freeze_support()
        with multiprocessing.Pool(n_workers, initializer=tqdm.tqdm.set_lock,
                                  initargs=(multiprocessing.RLock(),)) as pool:
            manager = ThreadManager(multiprocessing.Manager(), n_workers, 1, 1)
            func = functools.partial(_render_data, DATA_DIR, manager, parallel=parallel)
            num_segments = list(
                tqdm.tqdm(pool.imap_unordered(func, valid_data), total=len(valid_data), desc='Files', miniters=1,
                          position=0, maxinterval=1))

            # for recording_name, render_path in tqdm.tqdm(valid_renders, desc='Files'):
            #     num_segments_rendered += gen_sarsa_pairs(render_path, recording_name, DATA_DIR)
    except Exception as e:
        if isinstance(e, KeyboardInterrupt):
            pool.terminate()
            pool.join()
            raise e
        print("Exception in pool: ", type(e), e)
        print('Vectorized {} files in total!'.format(sum(num_segments)))
        raise e

    num_segments_rendered = sum(num_segments)

    print('Vectorized {} files in total!'.format(num_segments_rendered))
    if E('errors.txt'):
        print('Errors:')
        print(open('errors.txt', 'r').read())


def _make_tar(output_tar_path: str, folders: List[str]) -> None:
    with tarfile.open(output_tar_path, "w") as archive:
        logging.info(f'Generating archive {output_tar_path}')
        archive.add('VERSION')
        for folder in folders:
            archive.add(folder)


def package(out_dir=DATA_DIR):
    # Verify version
    if DATA_DIR is None:
        raise RuntimeError('MINERL_DATA_ROOT is not set!')
    with open(os.path.join(DATA_DIR, minerl.data.VERSION_FILE_NAME)) as version_file:
        version_file_num = int(version_file.readline())
        if minerl.data.DATA_VERSION != version_file_num:
            raise RuntimeError('Data version is out of date! MineRL data version is {} but VERSION file is {}'
                               .format(minerl.data.DATA_VERSION, version_file_num))

    logging.info("Writing tar files to {}".format(out_dir))
    os.makedirs(out_dir, exist_ok=True)

    # Collect experiment folders
    exp_folders = [f for f in os.listdir(DATA_DIR) if f.startswith('MineRL') and '.' not in f]
    basalt_folders = [f for f in exp_folders if "basalt" in f.lower()]
    diamond_folders = [f for f in exp_folders if f not in basalt_folders]

    os.chdir(out_dir)

    # Generate tar archives
    _make_tar(os.path.join(out_dir, 'basalt_data_texture_0_low_res.tar'), basalt_folders)
    _make_tar(os.path.join(out_dir, 'diamond_data_texture_0_low_res.tar'), diamond_folders)

    # Generate minimal tar archives using random subset from all experiment demos
    with tarfile.open(os.path.join(out_dir, 'data_texture_0_low_res_minimal.tar'), "w") as archive:
        logging.info('Generating archive {}'.format('data_texture_0_low_res_minimal.tar'))
        archive.add('VERSION')
        random.seed(minerl.data.DATA_VERSION)
        for folder in exp_folders:
            for _ in range(2):
                archive.add(J(folder, random.choice(os.listdir(J(DATA_DIR, folder)))))

    # Generate individual tar files
    for folder in exp_folders:
        with tarfile.open(J(out_dir, folder + '.tar'), "w") as archive:
            logging.info('Generating archive {}.tar'.format(folder))
            archive.add('VERSION')
            archive.add(folder)

    # Generate hash files
    logging.info('Generating hashes for all files')

    archives = [a for a in os.listdir(out_dir) if a.endswith('.tar')]

    with open(J(out_dir, 'MD5SUMS'), 'w') as md5_file, \
            open(J(out_dir, 'SHA1SUMS'), 'w') as sha1_file, \
            open(J(out_dir, 'SHA256SUMS'), 'w') as sha256_file:
        for archive in archives:
            logging.info('Generating hashes for {}'.format(archive))
            archive_dir = os.path.join(out_dir, archive)
            md5_file.write('{} {}\n'.format(hashlib.md5(open(archive_dir, 'rb').read()).hexdigest(), archive))
            sha1_file.write('{} {}\n'.format(hashlib.sha1(open(archive_dir, 'rb').read()).hexdigest(), archive))
            sha256_file.write('{} {}\n'.format(hashlib.sha256(open(archive_dir, 'rb').read()).hexdigest(), archive))


def main(parallel=True, n_workers=56, regex_pattern: Optional[str] = None):
    publish(parallel=parallel, n_workers=n_workers, regex_pattern=regex_pattern)
    package()


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    if len(sys.argv) > 1:
        if 'pub' in sys.argv[1]:
            publish()
        if 'pack' in sys.argv[1]:
            if len(sys.argv) > 2:
                package(out_dir=sys.argv[2])
            else:
                package()
    else:
        publish()
        package()
