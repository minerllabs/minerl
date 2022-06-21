# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
from minerl.herobraine.hero.handlers.agent.action import Action
import jinja2
import minerl.herobraine.hero.spaces as spaces
import numpy as np


class CameraAction(Action):
    """
    Uses <delta_pitch, delta_yaw> vector in degrees to rotate the camera. pitch range [-180, 180], yaw range [-180, 180]
    """

    def to_string(self):
        return 'camera'

    def xml_template(self) -> str:
        return str("<CameraCommands/>")

    def __init__(self):
        # TODO: Document and clean this wierd _ magic.
        self._command = 'camera'
        super().__init__(self.command, spaces.Box(low=-180, high=180, shape=[2], dtype=np.float32))

    def from_universal(self, x):
        if 'custom_action' in x and 'cameraYaw' in x['custom_action'] and 'cameraPitch' in x['custom_action']:
            delta_pitch = x['custom_action']['cameraPitch']
            delta_yaw = x['custom_action']['cameraYaw']
            assert not np.isnan(np.sum(x['custom_action']['cameraYaw'])), "NAN in action!"
            assert not np.isnan(np.sum(x['custom_action']['cameraPitch'])), "NAN in action!"
            return np.array([-delta_pitch, -delta_yaw], dtype=np.float32)
        else:
            return np.array([0.0, 0.0], dtype=np.float32)
