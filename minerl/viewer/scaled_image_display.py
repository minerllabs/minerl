# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import pyglet

try:
    from pyglet.gl import *
except ImportError as e:
    raise ImportError('''
    Error occured while running `from pyglet.gl import *`
    HINT: make sure you have OpenGL install. On Ubuntu, you can run 'apt-get install python-opengl'.
    If you're running on a server, you may need a virtual frame buffer; something like this should work:
    'xvfb-run -s \"-screen 0 1400x900x24\" python <your_script.py>'
    ''')

from gym.envs.classic_control import rendering


class ScaledImageDisplay(rendering.SimpleImageViewer):
    def __init__(self, width, height):
        super().__init__(None, 2700)

        if width > self.maxwidth:
            scale = self.maxwidth / width
            width = int(scale * width)
            height = int(scale * height)
        self.window = pyglet.window.Window(width=width, height=height,
                                           display=self.display, vsync=False, resizable=True)
        self.window.dispatch_events()
        self.window.switch_to()
        self.window.flip()
        self.width = width
        self.height = height
        self.isopen = True

        @self.window.event
        def on_resize(width, height):
            self.width = width
            self.height = height

        @self.window.event
        def on_close():
            self.isopen = False

    def blit_texture(self, arr, pos_x=0, pos_y=0, width=None, height=None):
        assert len(arr.shape) == 3, "You passed in an image with the wrong number shape"
        image = pyglet.image.ImageData(arr.shape[1], arr.shape[0],
                                       'RGB', arr.tobytes(), pitch=arr.shape[1] * -3)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        texture = image.get_texture()
        texture.width = width if width else self.width
        texture.height = height if height else self.height

        texture.blit(pos_x, pos_y)  # draw

    def imshow(self, arr):
        self.window.clear()
        self.window.switch_to()
        self.window.dispatch_events()
        self.blit_texture(arr)
        self.window.flip()
