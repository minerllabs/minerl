if __name__=="__main__":
    import pyglet
    import minerl
    import getch
    import argparse
    import logging
    import coloredlogs
    import time
    import tqdm 
    import numpy as np
    from gym.envs.classic_control import rendering

    coloredlogs.install(logging.DEBUG)
    logger = logging.getLogger(__name__)

    QUIT='q'
    FORWARD='k'
    BACK='j'
    SPEED_UP ='x'
    SLOWE_DOWN ='z'


    def parse_args():
        parser = argparse.ArgumentParser("MineRL Stream Viewer")
        parser.add_argument("environment", type=str)
        parser.add_argument("stream_name", type=str)

        return parser.parse_args()


    class Rect:
        def __init__(self, x, y, w, h, color=None):
            color = (255,255,255) if color is None else color
            self.set(x, y, w, h, color)

        def draw(self):
            pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, self._quad, self._color_str)

        def set(self, x=None, y=None, w=None, h=None, color=None):
            self._x = self._x if x is None else x
            self._y = self._y if y is None else y
            self._w = self._w if w is None else w
            self._h = self._h if h is None else h
            self._color = self._color if color is None else color
            self._quad = ('v2f', (self._x, self._y,
                        self._x + self._w, self._y,
                        self._x + self._w, self._y + self._h,
                        self._x, self._y + self._h))  
            self._color_str = ['c3B', self._color + self._color + self._color + self._color]

        @property
        def center(self):
            return self._x + self._w//2, self._y + self._h//2

        @property
        def height(self):
            return self._h

        @property 
        def width(self):
            return self._w

        def __repr__(self):
            return f"Rect(x={self._x}, y={self._y}, w={self._w}, h={self._h})"


    class Point:
        def __init__(self, x, y, radius, color=None):
            color = (255,255,255) if color is None else color
            self.set(x, y, radius, color)

        def draw(self):
            pyglet.graphics.draw_indexed(3, pyglet.gl.GL_TRIANGLES,
                [0, 1, 2],
                self._vertex,
                self._color_str)

            # pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, self._quad, self._color_str)

        def set(self, x=None, y=None, radius=None, color=None):
            self._x = self._x if x is None else x
            self._y = self._y if y is None else y
            self._radius = self._radius if radius is None else radius
            self._color = self._color if color is None else color

            height = self._radius/0.57735026919
            # TODO THIS IS INCORRECT LOL :) It's not a true radius.
            self._vertex = ('v2f', (self._x-self._radius, self._y - height/2,
                        self._x + self._radius, self._y -height/2,
                        self._x, self._y + height/2))  
            self._color_str = ['c3B', self._color + self._color +  self._color]

        def __repr__(self):
            return f"Point(x={self._x}, y={self._y}, w={self._w}, h={self._h})"



    class ScaledWindowImageViewer(rendering.SimpleImageViewer):
        def __init__(self, width, height):
            super().__init__(None, 640)

            if width > self.maxwidth:
                scale = self.maxwidth / width
                width = int(scale * width)
                height = int(scale * height)
            self.window = pyglet.window.Window(width=width, height=height, 
                display=self.display, vsync=False, resizable=True)            
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

    class ControlsViewer(ScaledWindowImageViewer):
        def __init__(self):
            super().__init__(600, 300)
            
            self.key_labels = self.make_key_labels()
            self.camera_rect = Rect(300,40, 200, 200, color=(36, 109, 94))
            self.camera_point = Point(*self.camera_rect.center, radius=10)

        def make_key_labels(self):
            keys = {}
            SZ = 40
            default_params = {  
                        "font_name": 'Courier New',
                        "font_size": 24,
                        "anchor_x":'center', "anchor_y":'center'}
            fo_x, fo_y = 0, SZ
            o_x, o_y = fo_x + SZ*3, fo_y + SZ*2 

            keys.update( {
                "forward": pyglet.text.Label('W', x=o_x, y= o_y + SZ, **default_params),
                "left": pyglet.text.Label('A', x=o_x - SZ, y= o_y , **default_params),
                "back": pyglet.text.Label('S', x=o_x , y= o_y , **default_params),
                "right": pyglet.text.Label('D', x=o_x + SZ, y= o_y , **default_params),
            })

            # sprint & sneak

            o_x, o_y = fo_x + SZ, fo_y
            keys.update({
                "sprint": pyglet.text.Label('spnt', x=o_x + SZ*3.5, y= o_y, **default_params),
                "sneak": pyglet.text.Label('snk', x=o_x , y= o_y , **default_params)})

            # jump
            o_x, o_y = fo_x + SZ*3, fo_y + SZ
            keys["jump"] = pyglet.text.Label('[ JUMP ]', x=o_x, y= o_y , **default_params)

            o_x, o_y = fo_x + SZ, fo_y
            keys["place"] = pyglet.text.Label('', x=o_x, y= o_y +SZ*6, **default_params)
            keys["craft"] = pyglet.text.Label('', x=o_x, y= o_y +SZ*5.4, **default_params)
            keys["nearbyCraft"] = pyglet.text.Label('', x=o_x, y= o_y +SZ*4.8, **default_params)
            keys["nearbySmelt"] = pyglet.text.Label('', x=o_x, y= o_y +SZ*4.2, **default_params)

            return keys

        def process_actions(self, action):
            for k in self.key_labels:
                self.key_labels[k].set_style('background_color', (0,0,0,0))

            USING_COLOR = (255,0,0,255)
            
            for x in action:
                try:
                    if action[x] > 0:
                        self.key_labels[x].set_style('background_color', USING_COLOR)
                except:
                    pass

            # Update mouse poisiton.
            delta_y, delta_x = action['camera'] 
            delta_x = np.clip(delta_x/60, -1,1)*self.camera_rect.width/2
            delta_y = np.clip(delta_y/60,-1,1)*self.camera_rect.height/2
            center_x, center_y = self.camera_rect.center

            if abs(delta_x) > 0 or abs(delta_y) > 0:
                camera_color = (162, 54, 69)
            else:
                camera_color = (255,255,255)
            self.camera_point.set(center_x + delta_x, center_y + delta_y, color=camera_color)
            # self.key_labels["a"].set_style('background_color', (255,255,0,255))

            for a, p in [
                ("place", "pl"),
                ("nearbyCraft", 'nC'),
                ("craft", 'c '),
                ("nearbySmelt", 'nS') ]:
                if a in action:
                    self.key_labels[a].set_style('font_size', 16)
                    self.key_labels[a].document.text = "{}: {}".format(p, action[a]) 
                else:
                    self.key_labels[a].document.text = ""


        def render_info(self, obs,reward,done,action):
            self.window.clear()
            self.window.switch_to()
            self.window.dispatch_events()

            self.process_actions(action)

            for label in self.key_labels:
                self.key_labels[label].draw()
            self.camera_rect.draw()
            self.camera_point.draw()
            self.window.flip()
        


    def main(opts):
        logger.info("Welcome to the MineRL Stream viewer! "
                    "Navigate through your file with 'j' (go back) 'k' (go forward)! To quit press `q`.")
        
        logger.info("Building data pipeline for {}".format(opts.environment))
        data = minerl.data.make(opts.environment)
        height, width = data.observation_space.spaces['pov'].shape[:2]

        controls_viewer = ControlsViewer()
        # controls_viewer.render_info(None, None, None, data.action_space.sample()); time.sleep(10); return
        video_viewer = ScaledWindowImageViewer(height*8, width*8)
        
        logger.info("Loading data for {}...".format(opts.stream_name))
        data_frames = list(data.load_data(opts.stream_name))
        file_len = len(data_frames)
        logger.info("Data loading complete!".format(opts.stream_name))
        

        indicator = tqdm.tqdm(total=file_len)
        key = ''
        position = 0
        speed = 1
        while key != QUIT:
            key = getch.getch()
            if key == FORWARD:
                new_position = min(position + speed, file_len -1)
            elif key == BACK:
                new_position = max(position -speed, 0)
            elif key == SPEED_UP:
                speed*=2
            elif key == SLOWE_DOWN:
                speed = max(1, speed //2)
                
            
            indicator.update(new_position - position)
            indicator.refresh()
            position = new_position

            # Display video viewer
            obs, rew, done, action = data_frames[position]
            video_viewer.imshow(obs["pov"])
            # Display info stuff!
            controls_viewer.render_info(obs,rew,done,action)

    main(parse_args())
