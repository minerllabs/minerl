from herobraine.hero.env_wrappers.env_wrapper_obs import WrapperObs
from gym.spaces.box import Box
from gym.spaces.tuple_space import Tuple
from herobraine.hero.handlers.observables import POVObservation
import numpy as np

class WrapperObsImagePlusVector(WrapperObs):
    def __init__(self, video_width=64, video_height=64, vector_len=1, time_feature=True):
        super().__init__()
        self.video_width = video_width
        self.video_height = video_height
        self.vector_len = vector_len
        self.time_feature = time_feature

    def get_obs_space(self):
        return Tuple([
            Box(low=0, high=1, shape=(self.video_width,
                                      self.video_height, 1), dtype=np.uint8),
            Box(low=0, high=1, shape=[self.vector_len], dtype=np.uint8)
        ])

    def _process_pov(self, pov):
        """
        Applies the appropriate normalization to the
        POV observations
        :param pov:
        :return:
        """
        return np.mean(pov.astype(np.uint8), axis=2)

    def convert_obs(self, raw_obs):
        (obs, elapsed) = raw_obs
        flat_actions = [obs[o] for o in obs if not isinstance(o, POVObservation)]
        
        if self.time_feature:  # add channel for time
            flat_actions.append(np.array(elapsed / 8000, dtype=np.float32))  # assuming 8000 tick episode len
        if len(flat_actions) == 0:
            flat_actions = np.ones(1, dtype=np.float32)

        return self._process_pov(obs[POVObservation]), np.concatenate(flat_actions, axis=None)
        
    def convert_multiple_obs(self, multiple_raw_obs):
        (multiple_obs, elapsed) = multiple_raw_obs
        return [self.convert_obs((obs, elapsed)) for obs in multiple_obs]
