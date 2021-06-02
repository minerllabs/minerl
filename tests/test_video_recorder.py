import gym
import minerl
import pytest
from tempfile import TemporaryDirectory
import os

#@pytest.mark.slow
def test_video_saves():
    print("Registered envs")
    print(gym.envs.registration.registry.env_specs.copy())
    with TemporaryDirectory() as tmpdir:
        env = gym.make("MineRLBasaltFindCaves-v0", video_record_path=os.path.join(tmpdir, 'video'))
        env.seed(63)
        obs = env.reset()
        assert obs in env.observation_space
        for _ in range(10):
            obs, rew, done, info = env.step(env.action_space.sample())
        dir_contents = os.listdir(os.path.join(tmpdir, 'video'))
        assert len(dir_contents) > 0
        assert 'mp4' in dir_contents[0]

if __name__ == "__main__":
    test_video_saves()