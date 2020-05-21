from herobraine.env_specs.navigate_specs import *
from herobraine.env_specs.treechop_specs import *
from herobraine.env_specs.obtain_diamond_specs import *
from herobraine.env_specs.obtain_iron_pickaxe_specs import *
from herobraine.env_specs.survival_specs import *

import gym
import minerl
from herobraine.hero.mc import INVERSE_KEYMAP

publishable_env_specs = [Navigate, NavigateDense, NavigateExtreme, NavigateExtremeDense, Treechop, ObtainIronPickaxe, ObtainIronPickaxeDense, ObtainDiamond, ObtainDiamondDense, SurvivalLimited]

def map_action_space(act):
    act_handlers = []
    for command_string in act.spaces:
        space = act.spaces[command_string]
        if command_string in INVERSE_KEYMAP:
            key_code = INVERSE_KEYMAP[command_string]
            handler = handlers.SingleKeyboardAction(command_string, key_code)
        elif command_string == handlers.PlaceBlock.to_string():
            item_list = space.values
            handler = handlers.PlaceBlock(item_list)
        elif command_string == handlers.Camera.to_string():
            handler = handlers.Camera()
        elif command_string == handlers.EquipItem.to_string():
            item_list = space.values
            handler = handlers.EquipItem(item_list)
        elif command_string == handlers.CraftItem.to_string():
            item_list = space.values
            handler = handlers.CraftItem(item_list)
        elif command_string == handlers.CraftItemNearby.to_string():
            item_list = space.values
            handler = handlers.CraftItemNearby(item_list)
        elif command_string == handlers.SmeltItemNearby.to_string():
            item_list = space.values
            handler = handlers.SmeltItemNearby(item_list)
        else:
            raise NotImplementedError('No string matched action handler {}'.format(command_string))
        act_handlers.append(handler)
    return act_handlers


def map_observation_space(obs, hand=None):
    obs_handlers = []
    observation_from_full_stats_added = False
    for command_string in obs.spaces:
        space = obs.spaces[command_string]
        if command_string == handlers.POVObservation.to_string():
            handler = handlers.POVObservation(space.shape)
        elif command_string == handlers.CompassObservation.to_string():
            handler = handlers.CompassObservation()
        elif command_string == handlers.CompassDistanceObservation.to_string():
            handler = handlers.CompassDistanceObservation()
        elif command_string == handlers.FlatInventoryObservation.to_string():
            item_list = list(space.spaces.keys())
            handler = handlers.FlatInventoryObservation(item_list)
        elif command_string == handlers.ObservationFromFullStats.to_string() or \
                command_string in handlers.ObservationFromFullStats.command_list():
            if not observation_from_full_stats_added:
                handler = handlers.ObservationFromFullStats()
                observation_from_full_stats_added = True
            else:
                continue
        elif command_string == 'equipped_items':
            for hand, sub_space in space.spaces.items():
                handler_list = map_observation_space(sub_space, hand=hand)
                for h in handler_list:
                    obs_handlers.append(h)
            continue
        elif command_string == handlers.TypeObservation.to_string():
            item_list = list(space.values)
            handler = handlers.TypeObservation('mainhand', item_list)
        elif command_string == handlers.DamageObservation.to_string():
            handler = handlers.DamageObservation('mainhand')
        elif command_string == handlers.MaxDamageObservation.to_string():
            handler = handlers.MaxDamageObservation('mainhand')
        else:
            raise NotImplementedError('No string matched observation handler {}'.format(command_string))
        obs_handlers.append(handler)
    return obs_handlers


def map_reward_space(name):
    for spec in publishable_env_specs:
        if spec().to_string() == name:
            return [hdl for hdl in spec().create_mission_handlers() if isinstance(hdl, handlers.RewardHandler)]
    raise NotImplementedError('No matching env spec found for ' + name)



def create_spec(gym_spec: gym.envs.registration.EnvSpec, folder: str, name: str):
    action_space = map_action_space(gym_spec._kwargs['action_space'])
    obs_space = map_observation_space(gym_spec._kwargs['observation_space'])
    rew_space = map_reward_space(name)
    spe =  {
        'action_space': action_space,
        'observation_space': obs_space,
        'reward_space': rew_space,
        'gym_spec': gym_spec,
        'env_folder': folder,
        'env_name': name
    }
    return spe


environments = list()
environments.append(('MineRLTreechop-v0', 'survivaltreechop'))
environments.append(('MineRLNavigate-v0', 'navigate'))
environments.append(('MineRLNavigateExtreme-v0', 'navigateextreme'))
environments.append(('MineRLNavigateDense-v0', 'navigate'))
environments.append(('MineRLNavigateExtremeDense-v0', 'navigateextreme'))
environments.append(('MineRLObtainIronPickaxe-v0', 'o_iron'))
environments.append(('MineRLObtainIronPickaxeDense-v0', 'o_iron'))
environments.append(('MineRLObtainDiamond-v0', 'o_dia'))
environments.append(('MineRLObtainDiamondDense-v0', 'o_dia'))
environments.append(('MineRLSurvivalLimited-v0', 'none'))
# environments.append(('MineRLSurvivalDiamond-v0', 'none'))

def get_publishable_environments():
    publishable_environments = [
        create_spec(gym.envs.registration.spec(name), folder, name) for name, folder in environments
    ]

    return publishable_environments
