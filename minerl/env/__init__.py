import os

# import gym
# Perform the registration.
from gym.envs.registration import register
from collections import OrderedDict
from minerl.env.core import MineRLEnv, missions_dir
from minerl.env.recording import MineRLRecorder, MINERL_RECORDING_PATH

from minerl.env.fake import FakeMineRLEnv