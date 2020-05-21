"""
render.py
# This script renders the merged experiments into
# actions and videos by doing the following
# 1) Unzipping various mcprs and building render directories
#    containing meta data.
# 2) Running the action_rendering scripts
# 3) Running the video_rendering scripts
"""
import logging
import subprocess
import traceback
import functools
import hashlib
import multiprocessing
import os
import random
import sys
import time

import math
import tqdm
import shutil
import numpy as np
import json
import signal
import tarfile

import herobraine.env_specs as envs
import herobraine.hero.handlers as handlers

import minerl

PUBLISHER_VERSION = minerl.data.DATA_VERSION

#######################
#      UTILITIES      #
#######################
from minerl_data.util.constants import (
    J, E,
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

FAILED_COMMANDS = []


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
        # If we have touched a pressure plate skip until we touch the next non air block
        elif touched_pressure_plate and len(obs['touched_blocks']) > 0:
            # print('\nTouched ground at {}'.format(tick))
            start_tick = tick
            break
        pass

    # Truncate the beginning of the episode (we align videos and unviersals by the end)
    if start_tick is None:
        # If we could not find a pressure_plate we may have started in the air - skip till we are on the ground
        on_ground_for = 0
        for tick, obs in universal.items():
            if len(obs['touched_blocks']) != 0:
                on_ground_for += 1
                if on_ground_for == 5:
                    start_tick = tick
                    # print('\nout of the air at {}'.format(tick))
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
        start_tick = 0
        print(len(universal.keys()))
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
def construct_data_dirs():
    """
    Constructs the render directories omitting
    elements on a blacklist.
    """
    print(DATA_DIR)
    if not E(DATA_DIR):
        os.makedirs(DATA_DIR)

    data_dirs = []
    for experiment_folder in tqdm.tqdm(next(os.walk(DATA_DIR))[1], desc='Directories', position=0):
        for experiment_dir in tqdm.tqdm(next(os.walk(J(DATA_DIR, experiment_folder)))[1], desc='Experiments',
                                        position=1):
            if not experiment_folder.startswith('MineRL') and \
                    'tempting_capers_shapeshifter-14' not in experiment_folder:
                # TODO: Add this to the list.
                data_dirs.append((experiment_dir, experiment_folder))
            # time.sleep(0.001)

    return data_dirs


def _render_data(output_root, manager, input_tuple):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    n = manager.get_index()
    recording_dir, experiment_folder = input_tuple
    ret = render_data(output_root, recording_dir, experiment_folder, lineNum=n)
    manager.free_index(n)
    return ret


# 2. render numpy format
def render_data(output_root, recording_dir, experiment_folder, lineNum=None):
    # Script to to pair actions with video recording
    # All times are in ms and we assume a actions list, a timestamp file, and a dis-synchronous mp4 video

    # Generate Numpy
    source_folder = J(DATA_DIR, experiment_folder, recording_dir)
    recording_source = J(source_folder, 'recording.mp4')
    universal_source = J(source_folder, 'univ.json')
    metadata_source = J(source_folder, 'metadata.json')

    # Gather all renderable environments for this experiment directory
    rendered_envs = 0
    filtered_environments = [
        env_spec for env_spec in envs.ENVS if env_spec.is_from_folder(experiment_folder)]

    for environment in filtered_environments:
        dest_folder = J(output_root, environment.name, 'v{}{}'.format(PUBLISHER_VERSION, recording_dir[len('g1'):]))
        recording_dest = J(dest_folder, 'recording.mp4')
        rendered_dest = J(dest_folder, 'rendered.npz')
        metadata_dest = J(dest_folder, 'metadata.json')

        # TODO remove to incrementally render files - during testing re-render each time
        if E(J(dest_folder, 'rendered.npz')):
            os.remove(J(dest_folder, 'rendered.npz'))

        # Don't render again, ensure source exits
        if E(rendered_dest):
            # TODO check universal_source exists
            continue

        # Don't render if files are missing
        if not E(source_folder) or not E(recording_source) or not E(universal_source or not E(metadata_source)):
            tqdm.tqdm.write('Files missing in ' + source_folder)
            continue

        # Load relevant handlers
        info_handlers = [obs for obs in environment.observables if not isinstance(obs, handlers.POVObservation)]
        reward_handlers = [r for r in environment.mission_handlers if isinstance(r, handlers.RewardHandler)]
        # done_handlers = [hdl for hdl in task.create_mission_handlers() if isinstance(hdl, handlers.QuitHandler)]
        action_handlers = environment.actionables

        # Process universal json
        with open(universal_source, 'r') as json_file:
            universal = json.load(json_file)

            universal = remove_initial_frames(universal)

            all_handlers = [hdl for sublist in [info_handlers, reward_handlers, action_handlers] for hdl in sublist]
            for hdl in all_handlers:
                try:
                    if "reset" in dir(hdl):
                        hdl.reset()
                except (NotImplementedError, AttributeError):
                    continue
            try:
                # info = {hdl.to_string(): np.array(
                #     [hdl.from_universal(universal[tick]) for tick in universal]) for hdl in info_handlers}
                # reward = np.array(
                #     [sum([hdl.from_universal(universal[tick]) for hdl in reward_handlers]) for tick in universal])
                # action = np.array(
                #     [hdl.from_universal(universal[tick]) for hdl in action_handlers for tick in universal])

                published = {'observation_' + hdl.to_string(): np.array(
                    [hdl.from_universal(universal[tick]) for tick in universal]) for hdl in info_handlers}
                published['reward'] = np.array(
                    [sum([hdl.from_universal(universal[tick]) for hdl in reward_handlers]) for tick in universal],
                    dtype=np.float32)[1:]
                published.update({'action_' + hdl.to_string(): np.array(
                    [hdl.from_universal(universal[tick]) for tick in universal])[1:] for hdl in action_handlers})


            except NotImplementedError as err:
                print('Exception:', repr(err), 'found with environment:', environment.name)
                raise err
                for hdl in all_handlers:
                    try:
                        hdl.from_universal({})
                    except NotImplementedError:
                        print("Missing from universal for command handler: ", hdl)
                        continue
                    except KeyError:
                        pass
                continue
            except KeyError:
                print("Key error in file - check from_universal for handlers")
                continue
            except Exception as e:
                print("caught exception:", repr(e))
                for hdl in all_handlers:
                    try:
                        for tick in universal:
                            hdl.from_universal(universal[tick])
                    except Exception as f:
                        print("Exception <", repr(f), "> for command handler:", hdl)
                        continue
                raise e

            # published = {'action': action, 'reward': reward, 'info': info}

        # Don't release ones with 1024 reward (they are bad streams)
        if not 'Survival' in environment.name:
            if sum(published['reward']) == 1024.0 and 'Obtain' in environment.name:
                print('skipping 1024 reward', environment.name)
                continue
            elif sum(published['reward']) < 64 and ('Obtain' not in environment.name):
                print('skipping less than 64 reward', environment.name)
                continue
            elif sum(published['reward']) == 0.0:
                print('skipping 0 reward', environment.name)
                continue
            elif sum(published['action_forward']) == 0:
                print('skipping 0 forward', environment.name)
                continue
            elif sum(published['action_attack']) == 0 and 'Navigate' not in environment.name:
                print('skipping 0 attack', environment.name)
                continue

        # Setup destination root
        if not E(dest_folder):
            try:
                os.makedirs(dest_folder, exist_ok=True)
            except OSError as exc:
                print('Could not make folder: ', dest_folder)
                raise exc

        # Render metadata
        try:
            with open(metadata_source, 'r') as meta_file:
                source = json.load(meta_file)
                metadata_out = {}
                if 'success' in source:
                    metadata_out['success'] = source['success']
                else:
                    metadata_out['success'] = False
                metadata_out['duration_ms'] = len(published['reward']) * 50  # source['end_time'] - source['start_time']
                metadata_out['duration_steps'] = len(published['reward'])
                metadata_out['total_reward'] = sum(published['reward'])
                metadata_out['stream_name'] = 'v{}{}'.format(PUBLISHER_VERSION, recording_dir[len('g1'):])
                with open(metadata_dest, 'w') as meta_file_out:
                    json.dump(metadata_out, meta_file_out)

            # Copy video if necessary
            if not E(recording_dest):
                shutil.copyfile(src=recording_source, dst=recording_dest)
            np.savez_compressed(rendered_dest, **published)
            rendered_envs += 1
        except (KeyError, ValueError) as e:
            print(e)
            shutil.rmtree(dest_folder, ignore_errors=True)
            continue

    print(rendered_envs)
    return rendered_envs


def publish():
    """
    The main render script.
    """
    valid_data = construct_data_dirs()
    print(valid_data)

    print("Publishing segments: ")
    numSegments = []
    if E('errors.txt'):
        os.remove('errors.txt')
    try:
        numW = 36

        multiprocessing.freeze_support()
        with multiprocessing.Pool(numW, initializer=tqdm.tqdm.set_lock, initargs=(multiprocessing.RLock(),)) as pool:
            manager = ThreadManager(multiprocessing.Manager(), numW, 1, 1)
            func = functools.partial(_render_data, DATA_DIR, manager)
            numSegments = list(
                tqdm.tqdm(pool.imap_unordered(func, valid_data), total=len(valid_data), desc='Files', miniters=1,
                          position=0, maxinterval=1))

            # for recording_name, render_path in tqdm.tqdm(valid_renders, desc='Files'):
            #     numSegmentsRendered += gen_sarsa_pairs(render_path, recording_name, DATA_DIR)
    except Exception as e:
        if isinstance(e, KeyboardInterrupt):
            pool.terminate()
            pool.join()
            raise e
        print('\n' * numW)
        print("Exception in pool: ", type(e), e)
        print('Vectorized {} files in total!'.format(sum(numSegments)))
        raise e
        if E('errors.txt'):
            print('Errors:')
            print(open('errors.txt', 'r').read())
        return

    numSegmentsRendered = sum(numSegments)

    print('\n' * numW)
    print('Vectorized {} files in total!'.format(numSegmentsRendered))
    if E('errors.txt'):
        print('Errors:')
        print(open('errors.txt', 'r').read())


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
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Collect experiment folders
    exp_folders = [f for f in os.listdir(DATA_DIR) if f.startswith('MineRL') and '.' not in f]

    # Generate tar archives
    os.chdir(DATA_DIR)
    with tarfile.open(os.path.join(out_dir, 'data_texture_0_low_res.tar.gz'), "w:gz") as archive:
        logging.info('Generating archive {}'.format('data_texture_0_low_res.tar.gz'))
        archive.add('VERSION')
        for folder in exp_folders:
            archive.add(folder)

    with tarfile.open(os.path.join(out_dir, 'data_texture_0_low_res_minimal.tar.gz'), "w:gz") as archive:
        logging.info('Generating archive {}'.format('data_texture_0_low_res_minimal.tar.gz'))
        archive.add('VERSION')
        random.seed(minerl.data.DATA_VERSION)
        for folder in exp_folders:
            for _ in range(5):
                archive.add(J(folder, random.choice(os.listdir(J(DATA_DIR, folder)))))

    # Generate individual tar files
    for folder in exp_folders:
        with tarfile.open(J(out_dir, folder + '.tar.gz'), "w:gz") as archive:
            logging.info('Generating archive {}.tar.gz'.format(folder))
            archive.add('VERSION')
            archive.add(folder)

    # Generate hash files
    # logging.info('Generating hashes for all files')
    # subprocess.run(['md5sum', '*.tar.gz', '>', J(out_dir, 'MD5SUMS')], cwd=out_dir)
    # subprocess.run(['sha1sum', 'MineRL*.tar.gz', '|', 'SHA1SUMS '])

    archives = [a for a in os.listdir(out_dir) if a.endswith('.tar.gz')]

    with open(J(out_dir, 'MD5SUMS'), 'w') as md5_file, \
            open(J(out_dir, 'SHA1SUMS'), 'w') as sha1_file, \
            open(J(out_dir, 'SHA256SUMS'), 'w') as sha256_file:
        for archive in archives:
            logging.info('Generating hashes for {}'.format(archive))
            archive_dir = os.path.join(out_dir, archive)
            md5_file.write('{} {}\n'.format(hashlib.md5(open(archive_dir, 'rb').read()).hexdigest(), archive))
            sha1_file.write('{} {}\n'.format(hashlib.sha1(open(archive_dir, 'rb').read()).hexdigest(), archive))
            sha256_file.write('{} {}\n'.format(hashlib.sha256(open(archive_dir, 'rb').read()).hexdigest(), archive))


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
