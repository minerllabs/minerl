# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import minerl.herobraine.envs as envs
from minerl.herobraine.wrappers.util import intersect_space


def _test_intersect_space(space, sample):
    intersected = intersect_space(space, sample)
    assert intersected in space


def test_obfuscated_envs():
    es = envs.obfuscated_envs
    for e in es:
        vector_e = e.env_to_wrap
        orig = vector_e.env_to_wrap
        for _ in range(100):
            o = vector_e.observation_space.sample()
            _test_intersect_space(orig.observation_space, vector_e.unwrap_observation(o))
        for _ in range(100):
            a = vector_e.action_space.sample()
            o = vector_e.unwrap_action(a)
            _test_intersect_space(orig.action_space, o)
