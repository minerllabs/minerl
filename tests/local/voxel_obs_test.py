from minerl.env.malmo import InstanceManager, MinecraftInstance
import minerl
import time
import gym
import numpy as np
import logging
import coloredlogs
from minerl.herobraine.env_specs.obtain_specs import ObtainDiamondDebug
import minerl.herobraine.hero.handlers as handlers

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
    # act(place='log') Test log 2
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
    [(act(jump=1), act(jump=1), act(jump=1), act(jump=1), act(jump=1), act(place='cobblestone'), act()) for _ in
     range(2)]
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

    [act() for _ in range(10)]

    return actions



class TestSpec(ObtainDiamondDebug):
    def create_observables(self):
        return super().create_observables() + [
            handlers.agent.VoxelObservation(limits=((-1,1), (-1,2), (-1,1)))
        ]



def test_voxel():
    env_spec = TestSpec(dense=False)

    env = env_spec.make()

    env.reset()

    total_reward  = 0
    for action in gen_obtain_debug_actions(env):
        obs, reward, done, info = env.step(action)

        total_reward += reward

    print("MISSION DONE")




if __name__ == '__main__':
    # test_wrapped_env()
    test_voxel()
