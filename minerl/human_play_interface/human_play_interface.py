# A simple pyglet app which controls the MineRL env,
# showing human the MineRL image and passing game controls
# to MineRL
# Intended for quick data collection without hassle or
# human corrections (agent plays but human can take over).

from typing import Optional
import time
from collections import defaultdict

import gym
from gym import spaces
import pyglet
import pyglet.window.key as key

# Mapping from MineRL action space names to pyglet keys
MINERL_ACTION_TO_KEYBOARD = {
    "ESC":       key.ESCAPE, # Used in BASALT to end the episode
    "attack":    pyglet.window.mouse.LEFT,
    "back":      key.S,
    "drop":      key.Q,
    "forward":   key.W,
    "hotbar.1":  key._1,
    "hotbar.2":  key._2,
    "hotbar.3":  key._3,
    "hotbar.4":  key._4,
    "hotbar.5":  key._5,
    "hotbar.6":  key._6,
    "hotbar.7":  key._7,
    "hotbar.8":  key._8,
    "hotbar.9":  key._9,
    "inventory": key.E,
    "jump":      key.SPACE,
    "left":      key.A,
    "pickItem":  pyglet.window.mouse.MIDDLE,
    "right":     key.D,
    "sneak":     key.LSHIFT,
    "sprint":    key.LCTRL,
    "swapHands": key.F,
    "use":       pyglet.window.mouse.RIGHT
}

KEYBOARD_TO_MINERL_ACTION = {v: k for k, v in MINERL_ACTION_TO_KEYBOARD.items()}


# Camera actions are in degrees, while mouse movement is in pixels
# Multiply mouse speed by some arbitrary multiplier
MOUSE_MULTIPLIER = 0.1

MINERL_FPS = 20
MINERL_FRAME_TIME = 1 / MINERL_FPS

class HumanPlayInterface(gym.Wrapper):
    def __init__(self, minerl_env):
        super().__init__(minerl_env)
        self._validate_minerl_env(minerl_env)
        self.env = minerl_env
        pov_shape = self.env.observation_space["pov"].shape
        self.window = pyglet.window.Window(
            width=pov_shape[1],
            height=pov_shape[0],
            vsync=False,
            resizable=False
        )
        self.start_time = time.time()
        self.end_time = time.time()
        self.pressed_keys = defaultdict(lambda: False)
        self.window.on_mouse_motion = self._on_mouse_motion
        self.window.on_mouse_drag = self._on_mouse_drag
        self.window.on_key_press = self._on_key_press
        self.window.on_key_release = self._on_key_release
        self.window.on_mouse_press = self._on_mouse_press
        self.window.on_mouse_release = self._on_mouse_release
        self.window.on_activate = self._on_window_activate
        self.window.on_deactive = self._on_window_deactivate
        self.window.dispatch_events()
        self.window.switch_to()
        self.window.flip()

        self.last_pov = None
        self.last_mouse_delta = [0, 0]

        self.window.clear()
        self._show_message("Waiting for reset.")

    def _on_key_press(self, symbol, modifiers):
        self.pressed_keys[symbol] = True

    def _on_key_release(self, symbol, modifiers):
        self.pressed_keys[symbol] = False

    def _on_mouse_press(self, x, y, button, modifiers):
        self.pressed_keys[button] = True

    def _on_mouse_release(self, x, y, button, modifiers):
        self.pressed_keys[button] = False

    def _on_window_activate(self):
        self.window.set_mouse_visible(False)
        self.window.set_exclusive_mouse(True)

    def _on_window_deactivate(self):
        self.window.set_mouse_visible(True)
        self.window.set_exclusive_mouse(False)

    def _on_mouse_motion(self, x, y, dx, dy):
        # Inverted
        self.last_mouse_delta[0] -= dy * MOUSE_MULTIPLIER
        self.last_mouse_delta[1] += dx * MOUSE_MULTIPLIER

    def _on_mouse_drag(self, x, y, dx, dy, button, modifier):
        # Inverted
        self.last_mouse_delta[0] -= dy * MOUSE_MULTIPLIER
        self.last_mouse_delta[1] += dx * MOUSE_MULTIPLIER

    def _validate_minerl_env(self, minerl_env):
        """Make sure we have a valid MineRL environment. Raises if not."""
        # Make sure action has right items
        remaining_buttons = set(MINERL_ACTION_TO_KEYBOARD.keys())
        remaining_buttons.add("camera")
        for action_name, action_space in minerl_env.action_space.spaces.items():
            if action_name not in remaining_buttons:
                raise RuntimeError(f"Invalid MineRL action space: action {action_name} is not supported.")
            elif (not isinstance(action_space, spaces.Discrete) or action_space.n != 2) and action_name != "camera":
                raise RuntimeError(f"Invalid MineRL action space: action {action_name} had space {action_space}. Only Discrete(2) is supported.")
            remaining_buttons.remove(action_name)
        if len(remaining_buttons) > 0:
            raise RuntimeError(f"Invalid MineRL action space: did not contain actions {remaining_buttons}")

        obs_space = minerl_env.observation_space
        if not isinstance(obs_space, spaces.Dict) or "pov" not in obs_space.spaces:
            raise RuntimeError("Invalid MineRL observation space: observation space must contain POV observation.")

    def _update_image(self, arr):
        self.window.switch_to()
        # Based on scaled_image_display.py
        image = pyglet.image.ImageData(arr.shape[1], arr.shape[0], 'RGB', arr.tobytes(), pitch=arr.shape[1] * -3)
        texture = image.get_texture()
        texture.blit(0, 0)
        self.window.flip()

    def _get_human_action(self):
        """Read keyboard and mouse state for a new action"""
        # Keyboard actions
        action = {
            name: int(self.pressed_keys[key] if key is not None else None) for name, key in MINERL_ACTION_TO_KEYBOARD.items()
        }

        action["camera"] = self.last_mouse_delta
        self.last_mouse_delta = [0, 0]
        return action

    def _show_message(self, text):
        label = pyglet.text.Label(
            text,
            font_size=32,
            x=self.window.width // 2,
            y=self.window.height // 2,
            anchor_x='center',
            anchor_y='center'
        )
        label.draw()
        self.window.flip()

    def reset(self):
        self.window.clear()
        self._show_message("Resetting environment...")
        obs = self.env.reset()
        self._update_image(obs["pov"])
        return obs

    def step(self, action: Optional[dict] = None, override_if_human_input: bool = False):
        """
        Step environment for one frame.

        If `action` is not None, assume it is a valid action and pass it to the environment.
        Otherwise read action from player (current keyboard/mouse state).

        If `override_if_human_input` is True, execeute action from the human player if they
        press any button or move mouse.

        The executed action will be added to the info dict as "taken_action".
        """
        self.end_time = time.time()
        time_to_sleep = MINERL_FRAME_TIME - (self.end_time - self.start_time)
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)
        self.start_time = time.time()
        if not action or override_if_human_input:
            self.window.dispatch_events()
            human_action = self._get_human_action()
            if override_if_human_input:
                if any(v != 0 if name != "camera" else (v[0] != 0 or v[1] != 0) for name, v in human_action.items()):
                    action = human_action
            else:
                action = human_action

        obs, reward, done, info = self.env.step(action)
        self._update_image(obs["pov"])

        if done:
            self._show_message("Episode done.")

        info["taken_action"] = action
        return obs, reward, done, info
