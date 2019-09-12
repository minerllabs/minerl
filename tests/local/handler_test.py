import minerl
import time
import gym
import numpy as np
import logging
import coloredlogs
coloredlogs.install(level=logging.DEBUG)


def gen_obtain_debug_actions(env):
    actions = []

    def act(**kwargs):
        action = env.action_space.no_op()
        for key, value in kwargs.items():
            action[key] = value
        actions.append(action)

    act(camera=np.array([45.0, 0.0], dtype=np.float32))

    # Testing craft handlers
    act(place='log')
    act()
    act(place='log2')
    act(craft='stick')
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
    [(act(jump=1), act(jump=1), act(jump=1), act(jump=1), act(jump=1), act(place='cobblestone'), act()) for _ in range(2)]
    act(equip='stone_pickaxe')
    [act(attack=1) for _ in range(40)]

    act(camera=np.array([-45.0, -90.0], dtype=np.float32))
    act(nearbyCraft='stone_axe')
    act(equip='stone_axe')

    # Test log reward
    act(camera=np.array([0.0, -90.0], dtype=np.float32))
    [act(attack=1) for _ in range(20)]
    [act(forward=1) for _ in range(10)]
    [act(attack=1) for _ in range(20)]
    [act(forward=1) for _ in range(10)]

    # Test empty equip command
    act(equip='air')

    # Test pickaxe reward
    act(camera=np.array([0.0, -90.0], dtype=np.float32))
    act(camera=np.array([0.0, -90.0], dtype=np.float32))

    act(craft='planks')
    act(craft='stick')
    act(craft='stick')
    act(nearbyCraft='iron_pickaxe')
    act(equip='iron_pickaxe')

    act(place='diamond_ore')    

    [act(attack=1) for _ in range(20)]
    [act(forward=1) for _ in range(10)]


    return actions


def test_env(environment='MineRLObtainTest-v0'):
    env = gym.make(environment)
    done = False

    for _ in range(4):
        env.reset()

        for action in gen_obtain_debug_actions(env):
            obs, reward, done, info = env.step(action)
            time.sleep(0.1)
            if reward != 0:
                print(reward)
                print(obs['inventory'])
            if done:
                break

        while not done:
            obs, reward, done, info = env.step(env.action_space.no_op())
            if reward != 0:
                print(reward)
        print("MISSION DONE")


if __name__ == '__main__':
    test_env()
