# ------------------------------------------------------------------------------------------------
# Copyright (c) 2018 Microsoft Corporation
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------
import os

from minerl.env.spaces import ActionSpace, StringActionSpace, VisualObservationSpace
from minerl.env.core import MineRLEnv, missions_dir
# Perform the registration.
from gym.envs.registration import  register



# TODO: REGISTER ENVS.
register(
    id='MineRLTreechop-v0',
    entry_point='minerl.env:MineRLEnv',
    kwargs={'xml': os.path.join(missions_dir, 'treechop.xml')},
    max_episode_steps=8000,
    reward_threshold=64.0,
)



__all__ = ['ActionSpace', 'StringActionSpace', 'VisualObservationSpace', 'Env', 'make']


