import os
import numpy as np
import logging

from minerl.env.core import MineRLEnv

J = os.path.join
E = os.path.exists


MINERL_RECORDING_PATH = os.environ.get('MINERL_RECORDING_PATH', None)

logger = logging.getLogger(__name__)


class MineRLRecorder(MineRLEnv):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.num_resets = 0
        self.reset_recording()


    def reset_recording(self):
        self.states = []
        self.next_states = []
        self.actions = []
        self.rewards = []


    def reset(self):
        obs_0 = super().reset()

        # handle recording
        # save out the recording if necessary.
        if self.rewards:
            # We have recorded something, and hence should save this out.
            self.save_recording()

        # Reset the recording at the end of the loop.
        self.num_resets += 1
        self.reset_recording()

        self.states.append(obs_0)
        return obs_0
        
    def step(self, action):
        next_state, reward, done, info = super().step(action)
        
        self.actions.append(action)
        self.rewards.append(reward)
        self.next_states.append(next_state)

        # For the next iteration.
        if not done:
            self.states.append(self.next_states[-1])

        return next_state, reward, done, info

    def save_recording(self):
        assert len(self.rewards) > 0    
        env_rec_dir = os.path.join(MINERL_RECORDING_PATH, self.spec.id)
        episode_dir = J(env_rec_dir, 
            "ep_{}".format(self.num_resets))

        if not E(episode_dir): os.makedirs(episode_dir)

        logger.debug("Saving recording to {}".format(episode_dir))

        np.save(J(episode_dir, 'states'), self.states)
        np.save(J(episode_dir, 'rewards'), self.rewards)
        np.save(J(episode_dir, 'next_states'), self.next_states)
        np.save(J(episode_dir, 'actions'), self.actions)

        logger.debug("Saved recording")
        

        


        

    


