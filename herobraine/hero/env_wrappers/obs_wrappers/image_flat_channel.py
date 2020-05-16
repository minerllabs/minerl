from herobraine.hero.env_wrappers.env_wrapper_obs import WrapperObs
from gym.spaces.box import Box
from gym.spaces.tuple_space import Tuple
from herobraine.hero.handlers.observables import POVObservation, CompassObservation, CompassDistanceObservation
import numpy as np

class WrapperObsImageFlatChannel(WrapperObs):
    def __init__(self, video_width=64, video_height=64, num_channels=4): 
        super().__init__()
        self.video_width = video_width
        self.video_height = video_height
        self.num_channels = num_channels

    def get_obs_space(self):
        return Box(low=0, high=1, shape=(self.video_width,
                                         self.video_height, self.num_channels), dtype=np.float32)

    def _process_pov(self, pov):
        """
        Applies the appropriate normalization to the
        POV observations
        :param pov:
        :return:
        """
        normalized_pov = np.mean(pov, axis=2) / 255
        return normalized_pov.astype(np.float32)

    def convert_obs(self, raw_obs):
        (obs, elapsed) = raw_obs

        elapsed_norm = elapsed / 8000
        time_channel = np.full((self.video_width, self.video_height), elapsed_norm, np.float32)
        obs_norm = self._process_pov(obs[POVObservation])

        compass_channel = None
        distance_channel = None
        for o in obs:
            if not isinstance(o, POVObservation):
                obs_value = (obs[o] - o.space.low) / (o.space.low + o.space.high)
                if isinstance(o, CompassObservation):
                    compass_channel = np.full((self.video_width, self.video_height), obs_value, np.float32)
                if isinstance(o, CompassDistanceObservation):
                    distance_channel = np.full((self.video_width, self.video_height), obs_value, np.float32)

        all_obs = [obs_norm, time_channel]
        if compass_channel is not None:
            all_obs.append(compass_channel)
        if distance_channel is not None:
            all_obs.append(distance_channel)

        return np.stack(all_obs, axis=2)
        
    def convert_multiple_obs(self, multiple_raw_obs):
        (multiple_obs, elapsed) = multiple_raw_obs
        return [self.convert_obs((obs, elapsed)) for obs in multiple_obs]
