# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

""" 
trajectory_display_controller.py -- Contains the main controller for interactive trajectory controllers.
"""
import time
import tqdm

import numpy as np
import subprocess
import os
import pyglet
import pyglet.window.key as key

from minerl.viewer.trajectory_display import HumanTrajectoryDisplay, VectorTrajectoryDisplay

QUIT = key.Q
FORWARD = key.RIGHT
BACK = key.LEFT
SPEED_UP = key.X
SLOW_DOWN = key.Z
FRAME_UP = key.UP
FRAME_DOWN = key.DOWN
FPS = 20.0
DEFAULT_INSTRUCTIONS = (
    "Instructions:\n"
    "   → - Go forward at speed \n"
    "   ← - Go back at speed \n"
    "   ↑ - Move forward 1 frame \n"
    "   ↓ - Move back 1 frame \n"
    "   X - Speed up 2X \n"
    "   Z - Slow down 2X \n"
    "   Q - Quit \n"
)


class TrajectoryDisplayController(object):
    """A class for controlling the trajectory display
    based on a sequence of data frames.
    """

    def __init__(self,
                 data_frames, header, subtext, instructions=DEFAULT_INSTRUCTIONS, cum_rewards=None,
                 vector_display=False):
        assert len(data_frames) > 0, "Empty dataframes provided."

        self.data_frames = data_frames
        self.position = 0
        self.speed = 1
        self.display = self._make_display(header, subtext, instructions, vector_display=vector_display)

    def _make_display(self, header, subtext, instructions, cum_rewards=None, vector_display=False):
        """Makes the trajectory display. Forms the reward plot from the data frames
        
        Args:
            header (str): The header of the individual trajectory
            subtext (str): The subtext of the trajectory.
            instructions (str): The default instructions.
        """

        cum_rewards = np.cumsum([x[2] for x in self.data_frames]) if cum_rewards is None else cum_rewards

        if not vector_display:
            return HumanTrajectoryDisplay(
                header, subtext, instructions=instructions,
                cum_rewards=cum_rewards)

        else:
            return VectorTrajectoryDisplay(
                header, subtext, instructions=instructions,
                cum_rewards=cum_rewards)

    def run(self, onFrameChange=None):
        """Runs the trajectory display controller. 
        
        Args:
            onFrameChange (lambda, optional): The call back for when the trajectory display changes the frame. This takes as arguments (position, data_frame[position]).
        """
        new_position = 0
        leave = False
        file_len = len(self.data_frames)

        while not leave:
            self.position = new_position

            # Display video viewer
            obs, action, rew, next_obs, done, meta = self.data_frames[self.position]

            self.display.render(obs, rew, done, action, self.position, file_len)

            if onFrameChange is not None:
                onFrameChange(self.position, self.data_frames[self.position])

            if QUIT in self.display.keys_down:
                leave = True
            elif FORWARD in self.display.keys_down:
                new_position = min(self.position + self.speed, file_len - 1)
            elif BACK in self.display.keys_down:
                new_position = max(self.position - self.speed, 0)
            elif FRAME_UP in self.display.keys_down:
                new_position = min(self.position + 1, len(self.data_frames) - 1)
                self.display.keys_down.remove(FRAME_UP)
            elif FRAME_DOWN in self.display.keys_down:
                new_position = max(self.position - 1, 0)
                self.display.keys_down.remove(FRAME_DOWN)
            elif SPEED_UP in self.display.keys_down:
                self.speed *= 2
                self.display.keys_down.remove(SPEED_UP)
            elif SLOW_DOWN in self.display.keys_down:
                self.speed = max(1, self.speed // 2)
                self.display.keys_down.remove(SLOW_DOWN)

            time.sleep(1 / FPS)

    def render(self, out_directory):
        buffs = []
        for i in tqdm.tqdm(range(len(self.data_frames))):
            obs, action, rew, next_obs, done, meta = self.data_frames[i]
            self.display.render(obs, rew, done, action, i, len(self.data_frames))

            pyglet.image.get_buffer_manager().get_color_buffer().save(
                os.path.join(out_directory, 'out{}.png'.format(i)))

        # Now convert them to a video
        subprocess.check_call(
            [
                "ffmpeg", "-y", "-r", "20",
                "-i", os.path.join(out_directory, "out%01d.png"),
                "-vcodec", "libx264", "-crf", "25", "-pix_fmt", "yuv420p",
                os.path.join(out_directory, "video.mp4")
            ])
