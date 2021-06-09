import gym
import minerl
import pytest
from tempfile import TemporaryDirectory
import os


@pytest.mark.slow
@pytest.mark.parametrize("env_name,save_video", [("MineRLBasaltFindCaves-v0", True),
                                            ("MineRLObtainDiamondDense-v0", True),
                                            ("MineRLBasaltFindCaves-v0", False),
                                            ("MineRLObtainDiamondDense-v0", False),
                                            ])
def test_video_saves(env_name, save_video):
    print("Registered envs")
    print(gym.envs.registration.registry.env_specs.copy())
    with TemporaryDirectory() as tmpdir:
        if save_video:
            env = gym.make(env_name, video_record_path=os.path.join(tmpdir, 'video'))
        else:
            env = gym.make(env_name)
        env.seed(63)
        obs = env.reset()
        assert obs in env.observation_space
        for _ in range(10):
            obs, rew, done, info = env.step(env.action_space.sample())
        _ = env.reset()
        env.close()
        video_path = os.path.join(tmpdir, 'video')

        if save_video:
            assert os.path.exists(video_path)
            dir_contents = os.listdir(video_path)
            assert len(dir_contents) > 0
            assert 'mp4' in dir_contents[0]
        else:
            assert not os.path.exists(video_path)


if __name__ == "__main__":
    test_video_saves()
