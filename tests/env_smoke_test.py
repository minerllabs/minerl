import gym
import pytest

import minerl
from minerl.herobraine import envs

ENV_NAMES = [env_spec.name for env_spec in envs.ENV_SPECS]
BASALT_ENV_NAMES = [env_spec.name for env_spec in envs.BASALT_COMPETITION_ENV_SPECS]


@pytest.mark.parametrize("env_name", ENV_NAMES)
def test_gym_spec_ok(env_name):
    gym.spec(env_name)


@pytest.mark.skip(reason='suspected as slow, > 5min. TODO (peterz) fix')
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


@pytest.mark.serial
@pytest.mark.parametrize("env_name", BASALT_ENV_NAMES)
def test_basalt_end_soon_after_snowball(env_name):
    """Basalt environment should terminate within 20 steps
    (really should only take
    13 steps = 10 steps snowball-episode-end-countdown + 3 steps Malmo equip delay,
    but adding some leeway here.
    )"""
    with gym.make(env_name) as env:
        obs = env.reset()
        throw_act = env.action_space.noop()
        throw_act["equip"] = "snowball"
        throw_act["use"] = 1
        for _ in range(20):
            obs, rew, done, info = env.step(throw_act)
            print(obs["inventory"]["snowball"])
            if done:
                break
        assert done
