from minerl.herobraine.hero.handlers.agent.action import Action
import minerl.herobraine.hero.spaces as spaces
import numpy as np


class MouseWheelAction(Action):
    """
    Handler for mouse wheel commands
    """

    def to_string(self):
        return 'dwheel'

    def xml_template(self) -> str:
        return str("<MouseWheel/>")

    def __init__(self):
        self._command = 'dwheel'
        # TODO the limits are arbitrary
        super().__init__(self.command, spaces.Box(low=-10, high=10, shape=[1], dtype=np.float32))
