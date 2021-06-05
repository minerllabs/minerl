import os
import pathlib

import numpy as np
from gym import Wrapper
import cv2


class _VideoWriter:
    """Helper class for writing MineRL images into mp4 video via `cv2`."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    def __init__(self, video_width, video_height, fps=20.0):
        self.video_width = video_width
        self.video_height = video_height
        self.fps = fps
        self.out = None

    def is_open(self):
        return self.out is not None

    def open(self, path):
        if self.is_open():
            raise ValueError("Call close() first.")
        self.out = cv2.VideoWriter(
            str(path),
            self.fourcc,
            self.fps,
            (self.video_height, self.video_width),
        )

    def write_rgb_image(self, img: np.ndarray):
        assert img.ndim == 3
        self.out.write(np.flip(img, axis=-1))

    def close(self):
        if self.out is not None:
            self.out.release()
            self.out = None


class VideoRecordingWrapper(Wrapper):
    """Writes obs['pov'] frames to an mp4 file inside `video_directory`, numbered
    by the episode number."""

    def __init__(self, env, video_directory):
        super().__init__(env)
        self.video_directory = pathlib.Path(video_directory)
        self.video_directory.mkdir(parents=True, exist_ok=True)
        self.video_num = 0  # Used for directory saving.

        video_dims = self.observation_space.spaces["pov"].shape
        self.video_writer = _VideoWriter(
            video_width=video_dims[0],
            video_height=video_dims[1],
            fps=20.0,
        )

    def step(self, action):
        obs, rew, done, info = super().step(action)
        self.video_writer.write_rgb_image(obs['pov'])
        return obs, rew, done, info

    def reset(self):
        """Closes the previous video stream, if one exists, and starts a new video stream."""
        if self.video_writer.is_open():
            self.video_writer.close()
        self.video_writer.open(self.get_video_out_path())
        self.video_num += 1

        obs = self.env.reset()
        self.video_writer.write_rgb_image(obs['pov'])
        return obs

    def get_video_out_path(self) -> pathlib.Path:
        result = self.video_directory / f"{self.video_num}.mp4"
        return result

    def close(self):
        self.video_writer.close()
        self.env.close()
