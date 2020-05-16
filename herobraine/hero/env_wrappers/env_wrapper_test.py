from herobraine.hero.env_wrappers.env_wrapper import HeroEnvWrapper
from herobraine.hero.env_wrappers.act_wrappers.discrete_limited \
    import WrapperActDiscrete
from herobraine.hero.env_wrappers.obs_wrappers.image_only \
    import WrapperObsSingle

from herobraine.tasks.treechop.task import TreechopTask
from typing import Any, Dict
import numpy as np

task = TreechopTask("TreechopTest", (64, 64), 6000, 20)
env = HeroEnvWrapper(task, WrapperActDiscrete(task.actionables), WrapperObsSingle())
s = env.reset()
d = False
while not d:
    s,r,d,_ = env.step(env.action_space.sample())
