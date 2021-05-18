from copy import deepcopy

import cv2
import numpy as np
from gym import ObservationWrapper

from minerl.herobraine.hero.spaces import Box, Dict


class DownscaleWrapper(ObservationWrapper):
    def __init__(self, env, downscale_res=(64, 64)):
        super().__init__(env)
        self.downscale_res = downscale_res

        obs_space = env.observation_space
        obs_dict = {key: obs_space[key] for key in obs_space.spaces.keys()}
        obs_dict['pov'] = Box(0, 255, downscale_res + (3,), dtype=np.uint8)
        self.observation_space = Dict(obs_dict)

    def observation(self, obs):
        scaled_obs = deepcopy(obs)
        scaled_obs['pov'] = cv2.resize(scaled_obs['pov'],
                                       self.downscale_res,
                                       interpolation=cv2.INTER_NEAREST)
        return scaled_obs
