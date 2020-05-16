from herobraine.hero.env_wrappers.env_wrapper_obs import WrapperObs
from gym.spaces.box import Box
from herobraine.hero.handlers.observables import POVObservation
import numpy as np

class WrapperObsImageOnly(WrapperObs):
    def __init__(self, video_width=64, video_height=64):
        super().__init__()
        self.video_width = video_width
        self.video_height = video_height

    def get_obs_space(self):
        return Box(low=0, high=1, shape=(self.video_width,
                                         self.video_height, 1), dtype=np.uint8),

    def convert_obs(self, raw_obs):
        for o in raw_obs:
            if isinstance(o, POVObservation):
                return np.mean(raw_obs[o], axis=2) / 255

    def convert_multiple_obs(self, multiple_raw_obs):
        return [self.convert_obs(raw_obs) for raw_obs in multiple_raw_obs]
