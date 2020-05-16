from herobraine.hero.env_wrappers.env_wrapper_act import WrapperAct
from gym.spaces.discrete import Discrete
import numpy as np

class WrapperActDiscrete(WrapperAct):
    def __init__(self, actionables, no_pitch, high_turn):
        super().__init__(actionables)
        self.no_pitch = no_pitch
        self.high_turn = high_turn

    def get_act_space(self):
        if self.no_pitch:
            return Discrete(8)
        else:
            return Discrete(10)

    def discretize_acts(self, actions):
        # Takes in a HandlerCollection actions, from human data
        # And discretizes it into the action space
        dict_to_action_obj = {
            action_obj.command: action_obj
            for action_obj in self.actionables
        } 
        if actions[dict_to_action_obj['jump']] == 1:
            return 3  # jump command
        if actions[dict_to_action_obj['move']] == -1:
            return 4
        if actions[dict_to_action_obj['move']] == 1:
            if actions[dict_to_action_obj['turn']] > 0:
                return 2
            if actions[dict_to_action_obj['turn']] < 0:
                return 0
            return 1
        if actions[dict_to_action_obj['pitch']] > 0:
            return 8
        if actions[dict_to_action_obj['pitch']] < 0:
            return 9
        else:
            if actions[dict_to_action_obj['turn']] > 0:
                return 7
            if actions[dict_to_action_obj['turn']] < 0:
                return 6
        return 5


    def convert_act(self, net_act):
        chosen_acts = {action_type: action_type.space.sample()
                       for action_type in self.actionables
                       }
        turn_amount = 0.1 if self.high_turn else 0.04
        t = 0
        j = 0
        p = 0
        m = 1
        u = 1
        if net_act == 0:
            t = -turn_amount
        elif net_act == 1:
            t = 0
        elif net_act == 2:
            t = turn_amount
        elif net_act == 3:
            j = 1
        elif net_act == 4:  # Move backwards
            m = -1
        elif net_act == 5:  # Stand still
            m = 0
        elif net_act == 6:  # Stand still turn left
            m = 0
            t = -turn_amount
        elif net_act == 7:  # Stand still turn right
            m = 0
            t = turn_amount
        elif not self.no_pitch:
            if net_act == 8:  # Stand still and pitch up
                m = 0
                p = turn_amount
            elif net_act == 9:  # Stand still and pitch down
                m = 0
                p = -turn_amount
        temp_action = {
            'move': np.array([m]),
            'attack': u,
            'strafe': np.array([0]),
            'pitch': np.array([p]),
            'turn': np.array([t]),
            'jump': j,
            'crouch': 0,
            'use': 0,              
        }
        for handler in chosen_acts.keys():
            chosen_acts[handler] = temp_action[handler.command]
        return chosen_acts

    # LIke convertAct, but for an array of actions
    def convert_acts(self, net_acts):
        return [self.convert_act(act) for act in net_acts]
