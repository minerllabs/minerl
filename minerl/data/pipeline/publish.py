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
import functools
import hashlib
import multiprocessing
import os
import random
import sys

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
def construct_data_dirs(black_list):
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
    return data_dirs


def _render_data(output_root, manager, input_tuple):
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
        env_spec for env_spec in envs.ENVS if env_spec.is_from_folder(experiment_folder)]
    # Don't render if files are missing
    if not E(source_folder) or not E(recording_source) or not E(universal_source) or not E(metadata_source):
        black_list.add(segment_str)
        return 0

    # Process universal json
    with open(universal_source, 'r') as json_file:
        universal = json.load(json_file)

        universal = remove_initial_frames(universal)

        for environment in filtered_environments:
            dest_folder = J(output_root, environment.name, 'v{}_{}'.format(PUBLISHER_VERSION, segment_str))
            recording_dest = J(dest_folder, 'recording.mp4')
            rendered_dest = J(dest_folder, 'rendered.npz')
            metadata_dest = J(dest_folder, 'metadata.json')


            # TODO remove to incrementally render files - during testing re-render each time
            if E(J(dest_folder, 'rendered.npz')):
                os.remove(J(dest_folder, 'rendered.npz'))

            # Don't render again, ensure source exits
            if E(rendered_dest):
                continue

            # Load relevant handlers
            info_handlers = [obs for obs in environment.observables if not isinstance(obs, handlers.POVObservation)]
            reward_handlers = [r for r in environment.mission_handlers if isinstance(r, handlers.RewardHandler)]
            # done_handlers = [hdl for hdl in task.create_mission_handlers() if isinstance(hdl, handlers.QuitHandler)]
            action_handlers = environment.actionables


            all_handlers = [hdl for sublist in [info_handlers, reward_handlers, action_handlers] for hdl in sublist]
            for hdl in all_handlers:
                try:
                    if "reset" in dir(hdl):
                        hdl.reset()
                except (NotImplementedError, AttributeError):
                    continue
            try:

                published = dict(
                    reward=np.array(
                        [sum([hdl.from_universal(universal[tick]) for hdl in reward_handlers]) for tick in universal],
                        dtype=np.float32)[1:])

                for tick in universal:
                    tick_data = {}
                    for _prefix, hdlrs in [
                        ("observation", info_handlers),
                        ("action", action_handlers)
                    ]:
                        if _prefix not in tick_data:
                            tick_data[_prefix] = OrderedDict()

                        for handler in hdlrs:
                            # Apply the handler from_universal to the universal[tick]
                            val = handler.from_universal(universal[tick])
                            assert val in handler.space, \
                                "{} is not in {} for handler {}".format(val, handler.space, handler.to_string)
                            tick_data[_prefix][handler.to_string()] = val

                        # Perhaps we can wrap here
                        if isinstance(environment, EnvWrapper):
                            if _prefix == "observation":
                                tick_data[_prefix]['pov'] = environment.observation_space['pov'].no_op()
                                tick_data[_prefix] = environment.wrap_observation(tick_data[_prefix])
                                del tick_data[_prefix]['pov']
                            elif _prefix == "action":
                                tick_data[_prefix] = environment.wrap_action(tick_data[_prefix])

                    tick_data = flatten(tick_data, sep='$')
                    for k, v in tick_data.items():
                        try:
                            published[k].append(v)
                        except KeyError:
                            published[k] = [v]

                # Adjust the action one forward (recall that the action packet is one off.)
                for k in published:
                    if k.startswith("action"):
                        published[k] = published[k][1:]

            except NotImplementedError as err:
                print('Exception:', str(err), 'found with environment:', environment.name)
                raise err
            except KeyError as err:
                print("Key error in file - check from_universal for handlers")
                print((err))
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

            # Don't release ones with 1024 reward (they are bad streams) and other smoke-tests
            if 'Survival' not in environment.name and not isinstance(environment, Obfuscated):
                # TODO these could be handlers instead!
                if sum(published['reward']) == 1024.0 and 'Obtain' in environment.name \
                        or sum(published['reward']) < 64 and ('Obtain' not in environment.name) \
                        or sum(published['reward']) == 0.0 \
                        or sum(published['action$forward']) == 0 \
                        or sum(published['action$attack']) == 0 and 'Navigate' not in environment.name:
                    black_list.add(segment_str)
                    print('Hey we should have blacklisted {} tyvm'.format(segment_str))
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
                    metadata_out['success'] = str(environment.determine_success_from_rewards(published['reward']))
                    metadata_out['duration_ms'] = len(published['reward']) * 50  # source['end_time'] - source['start_time']
                    metadata_out['duration_steps'] = len(published['reward'])
                    metadata_out['total_reward'] = sum(published['reward'])
                    metadata_out['stream_name'] = 'v{}{}'.format(PUBLISHER_VERSION, recording_dir[len('g1'):])
                    metadata_out['true_video_frame_count'] = calculate_frame_count(recording_dest)
                    with open(metadata_dest, 'w') as meta_file_out:
                        json.dump(metadata_out, meta_file_out)

                rendered_envs += 1
            except (KeyError, ValueError) as e:
                print(e)
                shutil.rmtree(dest_folder, ignore_errors=True)
                continue

    return rendered_envs


def publish():
    """
    The main render script.
    """
    num_w = 56

    black_list = Blacklist()
    valid_data = construct_data_dirs(black_list)
    print(valid_data)

    print("Publishing segments: ")
    num_segments = []
    if E('errors.txt'):
        os.remove('errors.txt')
    try:
        multiprocessing.freeze_support()
        with multiprocessing.Pool(num_w, initializer=tqdm.tqdm.set_lock, initargs=(multiprocessing.RLock(),)) as pool:
            manager = ThreadManager(multiprocessing.Manager(), num_w, 1, 1)
            func = functools.partial(_render_data, DATA_DIR, manager)
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
        print('\n' * num_w)
        print("Exception in pool: ", type(e), e)
        print('Vectorized {} files in total!'.format(sum(num_segments)))
        raise e

    num_segments_rendered = sum(num_segments)

    print('\n' * num_w)
    print('Vectorized {} files in total!'.format(num_segments_rendered))
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
    with tarfile.open(os.path.join(out_dir, 'data_texture_0_low_res.tar'), "w") as archive:
        logging.info('Generating archive {}'.format('data_texture_0_low_res.tar'))
        archive.add('VERSION')
        for folder in exp_folders:
            archive.add(folder)

    with tarfile.open(os.path.join(out_dir, 'data_texture_0_low_res_minimal.tar'), "w") as archive:
        logging.info('Generating archive {}'.format('data_texture_0_low_res_minimal.tar'))
        archive.add('VERSION')
        random.seed(minerl.data.DATA_VERSION)
        for folder in exp_folders:
            for _ in range(5):
                archive.add(J(folder, random.choice(os.listdir(J(DATA_DIR, folder)))))

    # Generate individual tar files
    for folder in exp_folders:
        with tarfile.open(J(out_dir, folder + '.tar'), "w") as archive:
            logging.info('Generating archive {}.tar'.format(folder))
            archive.add('VERSION')
            archive.add(folder)

    # Generate hash files
    # logging.info('Generating hashes for all files')
    # subprocess.run(['md5sum', '*.tar.gz', '>', J(out_dir, 'MD5SUMS')], cwd=out_dir)
    # subprocess.run(['sha1sum', 'MineRL*.tar.gz', '|', 'SHA1SUMS '])

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
