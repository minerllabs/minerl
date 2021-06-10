import gym
import minerl
import pytest
from tempfile import TemporaryDirectory
import os


@pytest.mark.slow
@pytest.mark.parametrize("env_name", ["MineRLBasaltFindCaves-v0", "MineRLObtainDiamondDense-v0"])
def test_video_saves(env_name):
    print("Registered envs")
    print(gym.envs.registration.registry.env_specs.copy())
    with TemporaryDirectory() as tmpdir:
        os.environ['VIDEO_RECORD_PATH'] = os.path.join(tmpdir, 'video')
        env = gym.make(env_name)
        env.seed(63)
        obs = env.reset()
        assert obs in env.observation_space
        for _ in range(10):
            obs, rew, done, info = env.step(env.action_space.sample())
        _ = env.reset()
        env.close()
        video_path = os.path.join(tmpdir, 'video')

        assert os.path.exists(video_path)
        dir_contents = os.listdir(video_path)
        assert len(dir_contents) > 0
        assert 'mp4' in dir_contents[0]



if __name__ == "__main__":
    test_video_saves()
