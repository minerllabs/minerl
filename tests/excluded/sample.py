import time

import minerl
import itertools
import gym
import sys
import numpy as np
import logging

import coloredlogs

coloredlogs.install(logging.DEBUG)

NUM_EPISODES = 4


def step_data(environment='MineRLObtainDiamond-v0'):
    d = minerl.data.make(environment)

    # Iterate through batches of data
    counter = 0
    for obs, act, rew, next_obs, done in d.sarsd_iter(num_epochs=-1, max_sequence_len=-1, queue_size=1, seed=1234):
        print("Act shape:", len(act), act)
        print("Obs shape:", len(obs), obs)
        print("Rew shape:", len(rew), rew)
        print(counter + 1)
        counter += 1


def gen_obtain_debug_actions(env):
    actions = []

    def act(**kwargs):
        action = env.action_space.noop()
        for key, value in kwargs.items():
            action[key] = value
        actions.append(action)

    act(camera=np.array([45.0, 0.0], dtype=np.float32))

    # Testing craft handlers
    act(place='log')
    act(craft='stick')
    act()
    act(craft='stick')  # Should fail - no more planks remaining
    act(craft='planks')
    act(craft='crafting_table')

    act(camera=np.array([0.0, 90.0], dtype=np.float32))

    # Testing nearbyCraft implementation (note crafting table must be in view of the agent)
    act(nearbyCraft='stone_pickaxe')  # Should fail - no crafting table in view
    act(place='crafting_table')
    act(nearbyCraft='stone_pickaxe')

    act(camera=np.array([0.0, 90.0], dtype=np.float32))

    # Testing nearbySmelt implementation (note furnace must be in view of the agent)
    act(nearbySmelt='iron_ingot')  # Should fail - no furnace in view
    act(place='furnace')
    act(nearbySmelt='iron_ingot')
    act(nearbySmelt='iron_ingot')
    act(nearbySmelt='iron_ingot')

    act(camera=np.array([45.0, 0.0], dtype=np.float32))

    # Test place mechanic (attack ground first to clear grass)
    act(attack=1)
    [(act(jump=1), act(jump=1), act(jump=1), act(jump=1), act(jump=1), act(place='cobblestone'), act()) for _ in
     range(2)]
    act(equip='stone_pickaxe')
    [act(attack=1) for _ in range(40)]

    act(camera=np.array([-45.0, -90.0], dtype=np.float32))
    act(nearbyCraft='stone_axe')
    act(equip='stone_axe')

    # Test log reward
    act(camera=np.array([0.0, -90.0], dtype=np.float32))
    [act(attack=1) for _ in range(40)]
    [act(forward=1) for _ in range(10)]

    act(camera=np.array([0.0, -90.0], dtype=np.float32))
    act(camera=np.array([0.0, -90.0], dtype=np.float32))

    act(craft='planks')
    act(craft='stick')
    act(craft='stick')
    act(nearbyCraft='iron_pickaxe')
    act()

    return actions


def test_env(environment='MineRLObtainTest-v0'):
    env = gym.make(environment)
    obs = env.reset()
    done = False
    acts = []
    print(obs)
    for action in gen_obtain_debug_actions(env):
        obs, reward, done, info = env.step(action)
        acts += [action]

        # print(np.sum(obs['pov']))
        if reward > 0:
            print("REWARD ============================= ")
            print("\n".join([str(x) for x in acts[-3:]]))
            print(reward)

        prev_act = action
        if done:
            break

    print("MISSION DONE")


def step_env(environment='MineRLObtainIronPickaxe-v0'):
    # Run random agent through environment
    env = gym.make(environment)  # or try 'MineRLNavigateDense-v0'

    for _ in range(NUM_EPISODES):
        obs = env.reset()
        done = False

        while not done:
            # This default action has only been added for MineRLObtainIronPickaxe-v0 so far
            action = env.action_space.noop()
            action['forward'] = env.action_space.spaces['forward'].sample()
            action['attack'] = 1
            action['place'] = env.action_space.spaces['place'].sample()
            obs, reward, done, info = env.step(action)
            if reward != 0:
                print(reward)
        print("MISSION DONE")

    print("Demo Complete.")


if __name__ == '__main__':
    if len(sys.argv) > 0 and sys.argv[1] == 'data':
        print("Testing data pipeline")
        if len(sys.argv) > 2 and not sys.argv[2] is None:
            step_data(sys.argv[2])
        else:
            step_data()
    elif len(sys.argv) > 0 and sys.argv[1] == 'env':
        print("Testing environment")
        if len(sys.argv) > 2 and not sys.argv[2] is None:
            step_env(sys.argv[2])
        else:
            step_env()
    elif len(sys.argv) > 0 and sys.argv[1] == 'test':
        test_env()
    else:
        print("Testing data pipeline")
        step_data()
        print("Testing environment")
        step_env()
