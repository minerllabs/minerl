from minerl.herobraine.hero import handlers
from typing import List
from minerl.herobraine.hero.handlers.translation import TranslationHandler
import time
from minerl.herobraine.env_specs.navigate_specs import Navigate

import coloredlogs
import logging

color = coloredlogs.install(level=logging.DEBUG)


# Let's also test monitors

class NavigateWithDistanceMonitor(Navigate):
    def create_monitors(self) -> List[TranslationHandler]:
        return [
            handlers.CompassObservation(angle=False, distance=True)
        ]


def _test_fake_env(env_spec, should_render=False):
    # Make the env.
    fake_env = env_spec.make(fake=True)

    assert fake_env.action_space == fake_env.task.action_space
    assert fake_env.observation_space == fake_env.observation_space

    assert fake_env._seed == None

    fake_env.seed(200)
    assert fake_env._seed == 200
    fake_obs = fake_env.reset()

    assert fake_obs in env_spec.observation_space

    for _ in range(100):
        fake_obs, _, _, fake_monitor = fake_env.step(fake_env.action_space.sample())
        if should_render:
            fake_env.render()
            time.sleep(0.1)
        assert fake_obs in env_spec.observation_space
        assert fake_monitor in env_spec.monitor_space


def test_fake_navigate():
    _test_fake_env(Navigate(dense=True, extreme=False))
    _test_fake_env(Navigate(dense=True, extreme=False, agent_count=3))


def test_fake_navigate_with_distance_monitor():
    task = NavigateWithDistanceMonitor(dense=True, extreme=False)
    fake_env = task.make(fake=True)
    _ = fake_env.reset()

    for _ in range(100):
        fake_obs, _, _, fake_monitor = fake_env.step(fake_env.action_space.sample())
        assert fake_monitor in fake_env.monitor_space
        assert "compass" in fake_monitor
        assert "distance" in fake_monitor["compass"]


if __name__ == "__main__":
    # _test_fake_env(Navigate(dense=True, extreme=False), should_render=True)
    _test_fake_env(Navigate(dense=True, extreme=False, agent_count=3), should_render=True)
    # test_fake_navigate_with_distance_monitor()
