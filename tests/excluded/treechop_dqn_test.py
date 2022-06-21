import gym
import itertools
import minerl
import numpy as np
import tensorflow as tf
import tensorflow.contrib.layers as layers
import tqdm
import baselines.common.tf_util as U

from baselines import logger
from baselines import deepq
from baselines.deepq.replay_buffer import ReplayBuffer
from baselines.common.schedules import LinearSchedule

import logging

import coloredlogs

coloredlogs.install(logging.DEBUG)

model = deepq.models.cnn_to_mlp(
    convs=[(32, 8, 4), (64, 4, 2), (64, 3, 1)],
    hiddens=[256],
    dueling=True
)


def action_wrapper(action_int):
    act = {
        "forward": 1,
        "back": 0,
        "left": 0,
        "right": 0,
        "jump": 0,
        "sneak": 0,
        "sprint": 0,
        "attack": 1,
        "camera": [0, 0],
        # "placeblock": 'none'
    }
    if action_int == 0:
        act['jump'] = 1
    elif action_int == 1:
        act['camera'] = [0, 10]
    elif action_int == 2:
        act['camera'] = [0, -10]
    elif action_int == 3:
        act['forward'] = 0

    return act.copy()


def observation_wrapper(obs):
    pov = obs['pov'].astype(np.float32) / 255.0 - 0.5
    # compass = obs['compassAngle']

    # compass_channel = np.ones(shape=list(pov.shape[:-1]) + [1], dtype=np.float32)*compass
    # compass_channel /= 180.0

    # return np.concatenate([pov, compass_channel], axis=-1)
    return pov


if __name__ == '__main__':
    with U.make_session(32):
        # Create the environment
        env = gym.make("MineRLTreechop-v0")
        spaces = env.observation_space.spaces['pov']
        shape = list(spaces.shape)
        # shape[-1] += 1

        # Create all the functions necessary to train the model
        act, train, update_target, debug = deepq.build_train(
            make_obs_ph=lambda name: U.BatchInput(shape
                                                  , name=name),
            q_func=model,
            num_actions=5,
            gamma=0.99,
            optimizer=tf.train.AdamOptimizer(learning_rate=1e-3),
        )
        # Create the replay buffer
        replay_buffer = ReplayBuffer(800000)
        # Create the schedule for exploration starting from 1 (every action is random) down to
        # 0.02 (98% of actions are selected according to values predicted by the model).
        exploration = LinearSchedule(schedule_timesteps=1000000, initial_p=1.0, final_p=0.02)

        # Initialize the parameters and copy them to the target network.
        U.initialize()
        update_target()

        episode_rewards = [0.0]
        obs = (env.reset())
        # obs = test_obs
        print(obs)

        obs = observation_wrapper(obs)

        for t in tqdm.tqdm(itertools.count()):
            # Take action and update exploration to the newest value
            # print(obs[None].shape)
            action = act(obs[None], update_eps=exploration.value(t))[0]

            new_obs, rew, done, _ = env.step(action_wrapper(action))
            # new_obs,  rew, done  = test_obs, 1, 0
            new_obs = observation_wrapper(new_obs)
            # Store transition in the replay buffer.
            replay_buffer.add(obs, action, rew, new_obs, float(done))
            obs = new_obs
            # print(new_obs)

            episode_rewards[-1] += rew
            if done:
                obs = env.reset()

                obs = observation_wrapper(obs)
                episode_rewards.append(0)

            is_solved = t > 100 and np.mean(episode_rewards[-101:-1]) >= 200
            if is_solved:
                # Show off the result
                env.render()
            else:
                # Minimize the error in Bellman's equation on a batch sampled from replay buffer.
                if t > 1000:
                    obses_t, actions, rewards, obses_tp1, dones = replay_buffer.sample(32)
                    train(obses_t, actions, rewards, obses_tp1, dones, np.ones_like(rewards))
                # Update target network periodically.
                if t % 1000 == 0:
                    update_target()

            if done and len(episode_rewards) % 1 == 0:
                logger.record_tabular("steps", t)
                logger.record_tabular("episodes", len(episode_rewards))
                logger.record_tabular("mean episode reward", round(np.mean(episode_rewards[-101:-1]), 1))
                logger.record_tabular("% time spent exploring", int(100 * exploration.value(t)))
                logger.dump_tabular()
