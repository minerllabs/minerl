import os
from copy import deepcopy

import numpy as np
from gym import Wrapper
from minerl.herobraine.hero.spaces import Box, Dict
import cv2


class VideoRecordingWrapper(Wrapper):
    def __init__(self, env, outfile=None, outdir=None,
                 downscale_res=(64, 64)):
        """

        """
        super().__init__(env)
        assert outfile or outdir, "Must include somewhere to save the video."
        assert not (outfile and outdir), "Can only choose one way to save videos."
        self.outfile = outfile
        self.outdir = outdir
        # Used for directory saving.
        self.current_index = 0

        obs_space = env.observation_space

        self.downscale_res = downscale_res
        if downscale_res is None:
            downscale_res = obs_space['pov'].shape[:2]

        obs_dict = {key: obs_space[key] for key in obs_space}
        obs_dict['pov'] = Box(0, 255, downscale_res + (3,),
                              dtype=np.uint8)
        self.observation_space = Dict(obs_dict)

        self.images = []

    def step(self, action):
        """ Saves the full image and returns a downscaled image. """
        obs, rew, done, info = super().step(action)
        self.images.append(obs['pov'])
        downscale_obs = deepcopy(obs)
        downscale_obs['pov'] = cv2.resize(downscale_obs['pov'],
                                          self.downscale_res,
                                          interpolation=cv2.INTER_NEAREST)
        return downscale_obs, rew, done, info

    def reset(self):
        if self.images:
            self.save_video()
            self.images = []
        return super().reset()

    def save_video(self):
        if self.outfile:
            write_mp4(self.images, self.outfile)
            self.outfile = None
        elif self.outdir:
            if not os.path.exists(self.outdir):
                os.makedirs(self.outdir)
            target_file = os.path.join(self.outdir, str(self.current_index) + ".mp4")
            self.current_index += 1
            write_mp4(self.images, self.outfile)


def write_mp4(images, target_file):
    print(images)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # Need to change the order of the input dimensions for CV2
    out = cv2.VideoWriter(target_file, fourcc, 20.0, (images[0].shape[1], images[0].shape[0]))

    for image in images:
        out.write(np.flip(image, axis=-1))  # cv2 uses BGR
    out.release()
    cv2.destroyAllWindows()