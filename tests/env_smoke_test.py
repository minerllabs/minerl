import gym
import pytest

import minerl
from minerl.herobraine import envs

ENV_NAMES = [env_spec.name for env_spec in envs.ENVS]


@pytest.mark.parametrize("env_name", ENV_NAMES)
def test_gym_spec_ok(env_name):
    gym.spec(env_name)


# @pytest.mark.skip(reason='suspected as slow, > 5min. TODO (peterz) fix')
@pytest.mark.parametrize("env_name", ENV_NAMES)
def test_envs_step_smoke(env_name):
    with gym.make(env_name) as env:
        obs = env.reset()
        assert obs in env.observation_space
        for _ in range(10):
            obs, rew, done, info = env.step(env.action_space.sample())
            assert isinstance(rew, float)
            assert isinstance(done, bool)
            assert isinstance(info, dict)
            assert obs in env.observation_space
