# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import logging
import coloredlogs
import time
import tqdm
import numpy as np
import pyglet

from minerl.viewer.scaled_image_display import ScaledImageDisplay
from minerl.viewer.primitives import Rect, Point
import abc

SZ = 35
BIG_FONT_SIZE = int(0.5 * SZ)
SMALL_FONT_SIZE = int(0.4 * SZ)
SMALLER_FONT_SIZE = int(0.35 * SZ)
USING_COLOR = (255, 0, 0, 255)
CAMERA_USING_COLOR = (162, 54, 69)
CUM_SUM_SPACE = .02


class TrajectoryDisplayBase(ScaledImageDisplay):

    def __init__(self, environment, stream_name="", instructions=None, cum_rewards=None):
        super().__init__(SZ * 28, SZ * 14)

        self.instructions = instructions
        self.f_ox, self.fo_y = SZ, SZ
        self.window.set_caption("{}: {}".format(environment, stream_name))
        self.cum_rewards = cum_rewards
        self.reward_height = int(SZ * 5 * 0.8)

        # Set up camera control stuff.
        cam_x = self.f_ox + SZ * 7
        cam_y = self.fo_y
        cam_size = self.reward_height
        self.camera_rect = Rect(cam_x, cam_y, cam_size, cam_size, color=(36, 109, 94))

        if self.instructions:
            self.make_instructions(environment, stream_name)

            self.keys_down = []

            @self.window.event
            def on_key_press(symbol, modifier):
                if symbol not in self.keys_down:
                    self.keys_down.append(symbol)

            @self.window.event
            def on_key_release(symbol, modifier):
                if symbol in self.keys_down:
                    self.keys_down.remove(symbol)
        if self.cum_rewards is not None:
            self.make_cum_reward_plotter()

    def make_instructions(self, environment, stream_name):
        if len(stream_name) >= 46:
            stream_name = stream_name[:44] + "..."

        self.instructions_labels = [
            pyglet.text.Label(environment, font_size=BIG_FONT_SIZE, y=self.height - SZ, x=SZ / 2, anchor_x='left'),
            pyglet.text.Label(stream_name, font_size=SMALLER_FONT_SIZE, font_name='Courier New', anchor_x='left',
                              x=1.4 * SZ, y=self.height - SZ * 1.5),
            pyglet.text.Label(self.instructions, multiline=True, width=12 * SZ, font_size=SMALLER_FONT_SIZE,
                              anchor_x='left', x=SZ / 2, y=self.height - SZ * 2.3),
        ]
        self.progress_label = pyglet.text.Label("", multiline=False, width=14 * SZ, font_name='Courier New',
                                                font_size=SMALLER_FONT_SIZE, anchor_x='left', x=14 * SZ, y=2)
        self.progress_label.set_style('background_color', (0, 0, 0, 255))
        self.meter = tqdm.tqdm()

    def make_cum_reward_plotter(self):
        # First let us matplot lib plot the cum rewards to an image.
        # Make a random plot...
        # plt.clf()

        import matplotlib
        import matplotlib.pyplot as plt

        matplotlib.use('Agg')
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(2, 2))
        ax = fig.add_subplot(111)

        plt.subplots_adjust(left=0.0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        # plt.title("Cumulative Rewards")

        # fig.patch.set_visible(False)
        # plt.gca().axis('off')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

        plt.plot(self.cum_rewards)
        plt.xticks([])
        plt.yticks([])
        self._total_space = len(self.cum_rewards) * (CUM_SUM_SPACE)
        plt.xlim(- self._total_space, len(self.cum_rewards) + self._total_space)

        # If we haven't already shown or saved the plot, then we need to
        # draw the figure first...
        fig.canvas.draw()

        # Now we can save it to a numpy array.

        data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))[:, :, :3]

        self.cum_reward_image = data

        # Create the rectangle.
        width = height = self.reward_height
        x, y = self.camera_rect.center
        y += int(self.reward_height // 2 + SZ * 2)
        x -= width // 2
        self.cum_reward_rect = Rect(x - 1, y - 1, width + 2, height + 2, color=(255, 255, 255))
        self.cum_reward_label = pyglet.text.Label(
            'Net Reward', font_size=SMALLER_FONT_SIZE, x=x + width // 2, y=y + height + 5,
            anchor_x='center', align='center')
        self.cum_reward_line = Rect(x, y, w=2, h=height, color=CAMERA_USING_COLOR)
        self.cum_reward_info_label = pyglet.text.Label('', multiline=True, width=width,
                                                       font_size=SMALLER_FONT_SIZE / 1.1, font_name='Courier New',
                                                       x=x + 3, y=y - 3, anchor_x='left', anchor_y='top')

    def update_reward_info(self, rew, step, max_step):
        self.cum_reward_line.set(x=self.cum_reward_rect.x + 1 + int(
            (step + self._total_space) / (max_step + self._total_space * 2) * (self.cum_reward_rect.width - 2)
        ))
        self.cum_reward_info_label.document.text = (
            "r(t): {0:.2f}\nnet:  {1:.2f}".format(rew, self.cum_rewards[step])
        )
        if rew > 0:
            self.cum_reward_info_label.set_style('color', (255, 0, 0, 255))
        else:
            self.cum_reward_info_label.set_style('color', (255, 255, 255, 255))

    def render(self, obs, reward, done, action, step, max):
        self.window.clear()
        self.window.switch_to()
        e = self.window.dispatch_events()

        self.blit_texture(obs["pov"], SZ * 14, 0, self.width - SZ * 14, self.width - SZ * 14)

        if action is not None:
            self.process_actions(action)
        self.process_observations(obs)

        if self.instructions:
            for label in self.instructions_labels:
                label.draw()
            prog_str = self.meter.format_meter(step, max, 0, ncols=52) + " " * 48

            self.progress_label.document.text = prog_str
            self.progress_label.draw()

        if self.cum_rewards is not None:
            self.update_reward_info(reward, step, max)
            self.cum_reward_label.draw()
            self.cum_reward_rect.draw()
            self.blit_texture(self.cum_reward_image,
                              self.cum_reward_rect.x + 1,
                              self.cum_reward_rect.y + 1,
                              width=self.cum_reward_rect.width - 2,
                              height=self.cum_reward_rect.height - 2)
            self.cum_reward_line.draw()
            self.cum_reward_info_label.draw()

        # Custom render loop.
        self._render(obs, reward, done, action, step, max)
        self.window.flip()

    @abc.abstractmethod
    def _render(self, obs, reward, done, action, step, max):
        pass

    @abc.abstractmethod
    def process_actions(actions):
        pass

    @abc.abstractmethod
    def process_observations(obs):
        pass


class HumanTrajectoryDisplay(TrajectoryDisplayBase):

    def __init__(self, environment, stream_name="", instructions=None, cum_rewards=None):
        super().__init__(environment, stream_name=stream_name, instructions=instructions, cum_rewards=cum_rewards)

        # Set up camera control stuff.
        cam_x = self.f_ox + SZ * 7
        cam_y = self.fo_y
        cam_size = self.reward_height
        self.camera_rect = Rect(cam_x, cam_y, cam_size, cam_size, color=(36, 109, 94))

        self.camera_labels = [
            pyglet.text.Label('Camera Control', font_size=SMALLER_FONT_SIZE, x=cam_x + cam_size / 2,
                              y=cam_y + cam_size + 2, anchor_x='center'),
            pyglet.text.Label('PITCH →', font_size=SMALLER_FONT_SIZE, font_name='Courier New', x=cam_x + cam_size / 2,
                              y=cam_y - SMALLER_FONT_SIZE - 4, anchor_x='center'),
            pyglet.text.Label('Y\nA\nW\n↓', font_size=SMALLER_FONT_SIZE, font_name='Courier New', multiline=True,
                              width=1, x=cam_x - SMALLER_FONT_SIZE - 2, y=cam_y + cam_size / 2, anchor_x='left')
        ]
        self.camera_labels[-1].document.set_style(0, len(self.camera_labels[-1].document.text),
                                                  {'line_spacing': SMALLER_FONT_SIZE + 2})
        self.camera_info_label = pyglet.text.Label('[0,0]', font_size=SMALLER_FONT_SIZE - 1, x=cam_x + cam_size,
                                                   y=cam_y, anchor_x='right', anchor_y='bottom')
        self.camera_point = Point(*self.camera_rect.center, radius=SZ / 4)

        self.key_labels = self.make_key_labels()

    def make_key_labels(self):
        keys = {}
        default_params = {
            "font_name": 'Courier New',
            "font_size": BIG_FONT_SIZE,
            "anchor_x": 'center', "anchor_y": 'center'}
        info_text_params = {
            "font_name": 'Courier New',
            "font_size": SMALL_FONT_SIZE,
            "anchor_y": 'center'
        }
        fo_x, fo_y = self.f_ox, self.fo_y
        o_x, o_y = fo_x + SZ * 3, fo_y + SZ * 2

        keys.update({
            "forward": pyglet.text.Label('↑', x=o_x, y=o_y + SZ, **default_params),
            "left": pyglet.text.Label('←', x=o_x - SZ, y=o_y + SZ / 2, **default_params),
            "back": pyglet.text.Label('↓', x=o_x, y=o_y, **default_params),
            "right": pyglet.text.Label('→', x=o_x + SZ, y=o_y + SZ / 2, **default_params),
        })

        keys["attack"] = pyglet.text.Label('attack', x=o_x + SZ * 1.5, y=o_y + SZ * 1.2, anchor_x='center',
                                           **info_text_params)

        # sprint & sneak

        o_x, o_y = fo_x + SZ, fo_y
        keys.update({
            "sprint": pyglet.text.Label('sprint', x=o_x + SZ * 3.5, y=o_y, anchor_x='center', **info_text_params),
            "sneak": pyglet.text.Label('sneak', x=o_x, y=o_y, anchor_x='center', **info_text_params)})

        # jump
        o_x, o_y = fo_x + SZ * 3, fo_y + SZ
        keys["jump"] = pyglet.text.Label('[ JUMP ]', x=o_x, y=o_y, anchor_x='center', **info_text_params)

        o_x, o_y = fo_x + SZ / 4, fo_y
        keys["place"] = pyglet.text.Label('', x=o_x, y=o_y + SZ * 6, anchor_x='left', **info_text_params)
        keys["craft"] = pyglet.text.Label('', x=o_x, y=o_y + SZ * 5.4, anchor_x='left', **info_text_params)
        keys["nearbyCraft"] = pyglet.text.Label('', x=o_x, y=o_y + SZ * 4.8, anchor_x='left', **info_text_params)
        keys["nearbySmelt"] = pyglet.text.Label('', x=o_x, y=o_y + SZ * 4.2, anchor_x='left', **info_text_params)

        return keys

    def process_actions(self, action):
        for k in self.key_labels:
            self.key_labels[k].set_style('color', (128, 128, 128, 255))

        for x in action:
            try:
                if action[x] > 0:
                    self.key_labels[x].set_style('color', USING_COLOR)
            except:
                pass

        # Update mouse poisiton.
        delta_y, delta_x = action['camera']
        self.camera_info_label.document.text = "[{0:.2f},{1:.2f}]".format(float(delta_y), float(delta_x))
        delta_x = np.clip(delta_x / 60, -1, 1) * self.camera_rect.width / 2
        delta_y = np.clip(delta_y / 60, -1, 1) * self.camera_rect.height / 2
        center_x, center_y = self.camera_rect.center

        if abs(delta_x) > 0 or abs(delta_y) > 0:
            camera_color = CAMERA_USING_COLOR
        else:
            camera_color = (255, 255, 255)
        self.camera_point.set(center_x + delta_x, center_y + delta_y, color=camera_color)
        # self.camera_info_label.set_style('color', list(camera_color)+ [255])

        # self.key_labels["a"].set_style('background_color', (255,255,0,255))

        for a, p in [
            ("place", "place      "),
            ("nearbyCraft", 'nearbyCraft'),
            ("craft", 'craft      '),
            ("nearbySmelt", 'nearbySmelt')]:
            if a in action:
                self.key_labels[a].set_style('font_size', SMALL_FONT_SIZE)
                self.key_labels[a].document.text = "{} {}".format(p, action[a])
            else:
                self.key_labels[a].document.text = ""

    def process_observations(self, obs):
        # TODO: ADD INVENTORY
        pass

    def _render(self, obs, reward, done, action, step, max):
        for label in self.key_labels:
            self.key_labels[label].draw()

        self.camera_rect.draw()
        for label in self.camera_labels:
            label.draw()
        self.camera_info_label.draw()
        self.camera_point.draw()


# Currently fixed size vector displays.
ACTION_VEC_SIZE = 64


class VectorTrajectoryDisplay(TrajectoryDisplayBase):

    def __init__(self, environment, stream_name="", instructions=None, cum_rewards=None):
        super().__init__(environment,
                         stream_name=stream_name,
                         instructions=instructions,
                         cum_rewards=cum_rewards)

        # Set up vectors
        cam_x = self.f_ox + SZ * 1.7
        cam_y = self.fo_y + SZ / 4
        self.vec_rec_height = int(SZ)
        self.vec_rec_width = int(SZ / 5.87)
        self.act_rects = [
            Rect(cam_x + int(self.vec_rec_width * 1.1 * i), cam_y, self.vec_rec_width, self.vec_rec_height,
                 color=(36, 109, 94))
            for i in range(ACTION_VEC_SIZE)]

        self.obs_rects = [
            Rect(cam_x + int(self.vec_rec_width * 1.1 * i), cam_y + self.vec_rec_height * 2.7, self.vec_rec_width,
                 self.vec_rec_height, color=(36, 109, 94))
            for i in range(ACTION_VEC_SIZE)]

        # Labels
        default_params = {
            "font_name": 'Courier New',
            "font_size": SMALL_FONT_SIZE - 2,
            "anchor_x": 'left', "anchor_y": 'center'}
        diff = 0
        self.act_label = pyglet.text.Label("action:", x=self.f_ox - SZ / 2, y=cam_y + int(self.vec_rec_height * diff),
                                           **default_params)
        self.state_label = pyglet.text.Label("state:", x=self.f_ox - SZ / 2,
                                             y=cam_y + self.vec_rec_height * 2.7 + int(self.vec_rec_height * diff),
                                             **default_params)

    def process_actions(self, action):
        action_vec = action['vector']

        for i, v in enumerate(action_vec):
            self.act_rects[i].set(h=int(self.vec_rec_height * v))
            self.act_rects[i].set(color=(36, 109, 94) if v > 0 else CAMERA_USING_COLOR)

    def process_observations(self, obs):
        action_vec = obs['vector']

        for i, v in enumerate(action_vec):
            self.obs_rects[i].set(h=int(self.vec_rec_height * v))
            self.obs_rects[i].set(color=(36, 109, 94) if v > 0 else CAMERA_USING_COLOR)

    def _render(self, obs, reward, done, action, step, max):
        for r in self.act_rects:
            r.draw()

        self.act_label.draw()
        self.state_label.draw()

        for r in self.obs_rects:
            r.draw()
