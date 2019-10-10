import minerl
import time
import gym
import numpy as np
import logging
import coloredlogs
coloredlogs.install(level=logging.DEBUG)
reward_dict = {
    "log": 1,
    "planks": 2,
    "stick": 4,
    "crafting_table": 4,
    "wooden_pickaxe": 8,
    "cobblestone": 16,
    "furnace": 32,
    "stone_pickaxe": 32,
    "iron_ore": 64,
    "iron_ingot": 128,
    "iron_pickaxe": 256,
    "diamond": 1024,
}


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
    act(nearbyCraft='furnace') 

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

    # Testing reward loop for crafting tables
    for _ in range(2):
        [act(attack=1) for _ in range(30)]
        [act(forward=1) for _ in range(10)]
        [act(back=1) for _ in range(10)]
        act(place='crafting_table')

    # Test log reward
    act(camera=np.array([0.0, -90.0], dtype=np.float32))
    [act(attack=1) for _ in range(20)]
    [act(forward=1) for _ in range(10)]

   # Test empty equip command
    act(equip='air')

    [act(attack=1) for _ in range(62)]
    [act(forward=1) for _ in range(10)]

 
    # Continue reward loop test with crafting table
    act(craft='planks')
    act(craft='crafting_table')
    act(place='crafting_table')

    # Test pickaxe reward
    act(camera=np.array([0.0, -90.0], dtype=np.float32))
    act(camera=np.array([0.0, -90.0], dtype=np.float32))

    act(craft='planks')
    act(craft='stick')
    act(craft='stick')
    act(nearbyCraft='iron_pickaxe')
    act(equip='iron_pickaxe')

    for _ in range(2):
        act(place='diamond_ore')    

        [act(attack=1) for _ in range(20)]
        [act(forward=1) for _ in range(10)]


    return actions

def test_dense_env():
    test_env('MineRLObtainTestDense-v0')

def test_env(environment='MineRLObtainTest-v0'):
    env = gym.make(environment)
    done = False
    inventories = []
    rewards = []
    for _ in range(10):
        env.reset()
        total_reward = 0
        print_next_inv = False

        for action in gen_obtain_debug_actions(env):
            for key, value in action.items():
                if isinstance(value, str) and value in reward_dict and key not in ['equip']:
                    print('Action of {}:{} if successful gets {}'.format(key, value, reward_dict[value]))
            obs, reward, done, info = env.step(action)

            if print_next_inv:
                print(obs['inventory'])
                print_next_inv = False

            # time.sleep(0.02)
            if reward != 0:
                print(obs['inventory'])
                print(reward)
                print_next_inv = True  
                total_reward += reward
            if done:
                break

        while not done:
            obs, reward, done, info = env.step(env.action_space.no_op())
            if reward != 0:
                print(reward)
        print("MISSION DONE")

        inventories.append(obs['inventory'])
        rewards.append(total_reward)

    time.sleep(0.2)
    for r, i in zip(inventories, rewards):
        print(r)
        print(i)
    
    if environment == 'MineRLObtainTest-v0':
        assert(all(r == 1482.0 for r in rewards))
    elif environment == 'MineRLObtainTestDense-v0':
        assert(all(r == 2874.0 for r in rewards))
    

if __name__ == '__main__':
    test_env()
    test_dense_env()

