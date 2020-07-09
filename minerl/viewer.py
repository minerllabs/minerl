"""A module for viewing individual streams from the dataset!

To use:
```
    python3 -m minerl.stream_viewier <environment name> <trajectory name>
```
"""

import argparse
from packaging import version
from  minerl.data import FILE_PREFIX

_DOC_TRAJ_NAME="{}absolute_zucchini_basilisk-13_36805-50154".format(FILE_PREFIX)

parser = argparse.ArgumentParser("python3 -m minerl.viewer")
parser.add_argument("environment", type=str, 
    help='The MineRL environment to visualize. e.g. MineRLObtainDiamondDense-v0')

parser.add_argument("stream_name", type=str,  nargs='?', default=None,
    help="(optional) The name of the trajectory to visualize. "
    "e.g. {}."
    "".format(_DOC_TRAJ_NAME))




if __name__=="__main__":
    import pyglet
    import minerl
    import sys
    import os
    if os.name == 'nt':
        import msvcrt
        getch = msvcrt
    else:
        import getch

    import random

        
    try:
        from pyglet.gl import *
    except ImportError as e:
        raise ImportError('''
        Error occured while running `from pyglet.gl import *`
        HINT: make sure you have OpenGL install. On Ubuntu, you can run 'apt-get install python-opengl'.
        If you're running on a server, you may need a virtual frame buffer; something like this should work:
        'xvfb-run -s \"-screen 0 1400x900x24\" python <your_script.py>'
        ''')


    import logging
    import coloredlogs
    import time
    import tqdm 
    import matplotlib
    matplotlib.use('Agg')
    import numpy as np
    import matplotlib.pyplot as plt

    plt.style.use('dark_background')
    # plt.ion()
    from gym.envs.classic_control import rendering

    coloredlogs.install(logging.DEBUG)
    logger = logging.getLogger(__name__)

    import pyglet.window.key as key

    def parse_args():
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
        def x(self):
            return self._x

        @property
        def y(self):
            return self._y

        @property
        def height(self):
            return self._h

        @property 
        def width(self):
            return self._w


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



    class ScaledWindowImageViewer(rendering.SimpleImageViewer):
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
                'RGB', arr.tobytes(), pitch=arr.shape[1]*-3)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, 
                gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
            texture = image.get_texture()
            texture.width = width if width else self.width
            texture.height = height if height else self.height
            
            texture.blit(pos_x, pos_y) # draw

        def imshow(self, arr):
            self.window.clear()
            self.window.switch_to()
            self.window.dispatch_events()
            self.blit_texture(arr)
            self.window.flip()

    SZ = 35
    BIG_FONT_SIZE = int(0.5*SZ)
    SMALL_FONT_SIZE=int(0.4*SZ)
    SMALLER_FONT_SIZE=int(0.35*SZ)
    USING_COLOR = (255,0,0,255)
    CAMERA_USING_COLOR =(162, 54, 69)
    CUM_SUM_SPACE  = .02
    class SampleViewer(ScaledWindowImageViewer):
        
        def __init__(self, environment, stream_name="", instructions=None, cum_rewards=None):
            super().__init__(SZ*28, SZ*14)
            
            self.instructions = instructions
            self.f_ox, self.fo_y = SZ, SZ
            self.key_labels = self.make_key_labels()
            self.window.set_caption("{}: {}".format(environment, stream_name))
            self.cum_rewards = cum_rewards
            

            # Set up camera control stuff.
            cam_x = self.f_ox + SZ*7
            cam_y = self.fo_y
            cam_size = int(SZ*5*0.8)
            self.camera_rect = Rect(cam_x,cam_y, cam_size, cam_size, color=(36, 109, 94))
            self.camera_labels = [
                pyglet.text.Label('Camera Control', font_size=SMALLER_FONT_SIZE, x= cam_x + cam_size/2, y= cam_y + cam_size +2, anchor_x='center'),
                pyglet.text.Label('PITCH →', font_size=SMALLER_FONT_SIZE,font_name='Courier New', x= cam_x + cam_size/2, y= cam_y - SMALLER_FONT_SIZE- 4, anchor_x='center'),
                pyglet.text.Label('Y\nA\nW\n↓', font_size=SMALLER_FONT_SIZE,  font_name='Courier New', multiline=True,width=1, x= cam_x - SMALLER_FONT_SIZE -2, y= cam_y +cam_size/2, anchor_x='left')
            ]
            self.camera_labels[-1].document.set_style(0, len(self.camera_labels[-1].document.text),{'line_spacing': SMALLER_FONT_SIZE+2} )
            self.camera_info_label = pyglet.text.Label('[0,0]', font_size=SMALLER_FONT_SIZE-1, x= cam_x + cam_size, y= cam_y, anchor_x='right', anchor_y='bottom')
            self.camera_point = Point(*self.camera_rect.center, radius=SZ/4)

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
                pyglet.text.Label(environment, font_size=BIG_FONT_SIZE, y = self.height-SZ, x = SZ/2, anchor_x='left'),
                pyglet.text.Label(stream_name, font_size=SMALLER_FONT_SIZE, font_name= 'Courier New', anchor_x='left', x=1.4*SZ, y= self.height-SZ*1.5),
                pyglet.text.Label(self.instructions,  multiline=True, width=12*SZ, font_size=SMALLER_FONT_SIZE, anchor_x='left', x= SZ/2, y= self.height-SZ*2.3),
            ]
            self.progress_label = pyglet.text.Label("",  multiline=False, width=14*SZ, font_name='Courier New', font_size=SMALLER_FONT_SIZE, anchor_x='left', x= 14*SZ, y= 2)
            self.progress_label.set_style('background_color', (0,0,0,255))
            self.meter = tqdm.tqdm()


        def make_cum_reward_plotter(self):
            # First let us matplot lib plot the cum rewards to an image.
            # Make a random plot...
            # plt.clf()
            fig = plt.figure(figsize=(2,2))
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
            self._total_space = len(self.cum_rewards)*(CUM_SUM_SPACE)
            plt.xlim(- self._total_space, len(self.cum_rewards) + self._total_space)

            # If we haven't already shown or saved the plot, then we need to
            # draw the figure first...
            fig.canvas.draw()

            # Now we can save it to a numpy array.

            data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
            data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))[:, :, :3]

            self.cum_reward_image =data
            
            # Create the rectangle.
            width = height = int(self.camera_rect.height)
            x,y = self.camera_rect.center
            y += int(self.camera_rect.height//2 + SZ*2)
            x -= width//2
            self.cum_reward_rect = Rect(x-1,y-1, width+2,height+2, color=(255, 255, 255))
            self.cum_reward_label = pyglet.text.Label(
                'Net Reward', font_size=SMALLER_FONT_SIZE, x=x+width//2, y=y+height+5,
            anchor_x='center', align='center')
            self.cum_reward_line = Rect(x, y, w=2, h=height, color=CAMERA_USING_COLOR)
            self.cum_reward_info_label = pyglet.text.Label('', multiline=True, width=width, 
                font_size=SMALLER_FONT_SIZE/1.1, font_name='Courier New', x=x+3, y=y-3, anchor_x='left', anchor_y='top')


        def update_reward_info(self, rew, step, max_step):
            self.cum_reward_line.set(x=self.cum_reward_rect.x+ 1 + int(
                (step + self._total_space)/(max_step + self._total_space*2)*(self.cum_reward_rect.width-2)
                ))
            self.cum_reward_info_label.document.text = (
                "r(t): {0:.2f}\nnet:  {1:.2f}".format(rew, self.cum_rewards[step])
            )
            if rew > 0:
                self.cum_reward_info_label.set_style('color', (255,0,0,255))
            else:
                self.cum_reward_info_label.set_style('color', (255,255,255,255))

        def make_key_labels(self):
            keys = {}
            default_params = {  
                        "font_name": 'Courier New',
                        "font_size": BIG_FONT_SIZE,
                        "anchor_x":'center', "anchor_y":'center'}
            info_text_params = {
                "font_name": 'Courier New',
                "font_size": SMALL_FONT_SIZE,
                 "anchor_y":'center'
            }
            fo_x, fo_y = self.f_ox, self.fo_y
            o_x, o_y = fo_x + SZ*3, fo_y + SZ*2 

            keys.update( {
                "forward": pyglet.text.Label('↑', x=o_x, y= o_y + SZ, **default_params),
                "left": pyglet.text.Label('←', x=o_x - SZ, y= o_y + SZ/2 , **default_params),
                "back": pyglet.text.Label('↓', x=o_x , y= o_y , **default_params),
                "right": pyglet.text.Label('→', x=o_x + SZ, y= o_y +SZ/2, **default_params),
            })

            keys["attack"] = pyglet.text.Label('attack', x=o_x + SZ*1.5, y= o_y +SZ*1.2 ,anchor_x='center',  **info_text_params)

            # sprint & sneak

            o_x, o_y = fo_x + SZ, fo_y
            keys.update({
                "sprint": pyglet.text.Label('sprint', x=o_x + SZ*3.5, y= o_y, anchor_x='center',  **info_text_params),
                "sneak": pyglet.text.Label('sneak', x=o_x , y= o_y ,anchor_x='center', **info_text_params)})

            # jump
            o_x, o_y = fo_x + SZ*3, fo_y + SZ
            keys["jump"] = pyglet.text.Label('[ JUMP ]', x=o_x, y= o_y ,anchor_x='center',  **info_text_params)

            o_x, o_y = fo_x + SZ/4, fo_y
            keys["place"] = pyglet.text.Label('', x=o_x, y= o_y +SZ*6, anchor_x='left', **info_text_params)
            keys["craft"] = pyglet.text.Label('', x=o_x, y= o_y +SZ*5.4, anchor_x='left', **info_text_params)
            keys["nearbyCraft"] = pyglet.text.Label('', x=o_x, y= o_y +SZ*4.8,anchor_x='left', **info_text_params)
            keys["nearbySmelt"] = pyglet.text.Label('', x=o_x, y= o_y +SZ*4.2,anchor_x='left', **info_text_params)

            return keys

        def process_actions(self, action):
            for k in self.key_labels:
                self.key_labels[k].set_style('color', (128,128,128,255))

            
            for x in action:
                try:
                    if action[x] > 0:
                        self.key_labels[x].set_style('color', USING_COLOR)
                except:
                    pass

            # Update mouse poisiton.
            delta_y, delta_x = action['camera'] 
            self.camera_info_label.document.text = "[{0:.2f},{1:.2f}]".format(float(delta_y), float(delta_x))
            delta_x = np.clip(delta_x/60, -1,1)*self.camera_rect.width/2
            delta_y = np.clip(delta_y/60,-1,1)*self.camera_rect.height/2
            center_x, center_y = self.camera_rect.center

            if abs(delta_x) > 0 or abs(delta_y) > 0:
                camera_color = CAMERA_USING_COLOR
            else:
                camera_color = (255,255,255)
            self.camera_point.set(center_x + delta_x, center_y + delta_y, color=camera_color)
            # self.camera_info_label.set_style('color', list(camera_color)+ [255])
            
            # self.key_labels["a"].set_style('background_color', (255,255,0,255))

            for a, p in [
                ("place", "place      "),
                ("nearbyCraft", 'nearbyCraft'),
                ("craft", 'craft      '),
                ("nearbySmelt", 'nearbySmelt') ]:
                if a in action:
                    self.key_labels[a].set_style('font_size', SMALL_FONT_SIZE)
                    self.key_labels[a].document.text = "{} {}".format(p, action[a]) 
                else:
                    self.key_labels[a].document.text = ""


        def render(self, obs,reward, done,action, step, max):
            self.window.clear()
            self.window.switch_to()
            e = self.window.dispatch_events()
            
            self.blit_texture(obs["pov"], SZ*14, 0, self.width -SZ*14, self.width -SZ*14)
            self.process_actions(action)

            for label in self.key_labels:
                self.key_labels[label].draw()

            self.camera_rect.draw()
            for label in self.camera_labels:
                label.draw()
            self.camera_info_label.draw()
            self.camera_point.draw()
            
            if self.instructions:
                for label in self.instructions_labels:
                    label.draw()
                prog_str = self.meter.format_meter(step, max, 0, ncols=52) + " "*48
            
                self.progress_label.document.text =  prog_str
                self.progress_label.draw()

            if self.cum_rewards is not None:
                self.update_reward_info(reward, step,max)
                self.cum_reward_label.draw()
                self.cum_reward_rect.draw()
                self.blit_texture(self.cum_reward_image, 
                    self.cum_reward_rect.x+1,
                    self.cum_reward_rect.y+1,
                    width=self.cum_reward_rect.width-2,
                    height= self.cum_reward_rect.height-2)
                self.cum_reward_line.draw()
                self.cum_reward_info_label.draw()

                
            self.window.flip()

    QUIT=key.Q
    FORWARD=key.RIGHT
    BACK=key.LEFT
    SPEED_UP =key.X
    SLOWE_DOWN =key.Z
    FRAME_UP = key.UP
    FRAME_DOWN = key.DOWN

    def main(opts):
        instructions_txt = (
            "Instructions:\n"
            "   → - Go forward at speed \n"
            "   ← - Go back at speed \n"
            "   ↑ - Move forward 1 frame \n"
            "   ↓ - Move back 1 frame \n"
            "   X - Speed up 2X \n"
            "   Z - Slow down 2X \n"
            "   Q - Quit \n"
        )
        logger.info("Welcome to the MineRL Stream viewer! \n" + instructions_txt)
        
        logger.info("Building data pipeline for {}".format(opts.environment))
        data = minerl.data.make(opts.environment)

        # for _ in data.seq_iter( 1, -1, None, None, include_metadata=True):
        #     print(_[-1])
        #     pass
        if opts.stream_name == None:
            trajs = data.get_trajectory_names()
            opts.stream_name = random.choice(trajs)
        
        logger.info("Loading data for {}...".format(opts.stream_name))
        data_frames = list(data.load_data(opts.stream_name, include_metadata=True))
        meta = data_frames[0][-1] 
        cum_rewards = np.cumsum([x[2] for x in data_frames])
        file_len = len(data_frames)
        logger.info("Data loading complete!".format(opts.stream_name))
        logger.info("META DATA: {}".format(meta))

        height, width = data.observation_space.spaces['pov'].shape[:2]

        controls_viewer = SampleViewer(opts.environment, opts.stream_name, 
            instructions=instructions_txt, cum_rewards=cum_rewards)
        

        indicator = tqdm.tqdm(total=file_len)
        key = ''
        position = 0
        speed = 1
        new_position = 0
        leave = False


        
        while not leave:
            indicator.update(new_position - position)
            indicator.refresh()
            position = new_position

            # Display video viewer
            obs, action, rew, next_obs, done, meta = data_frames[position]
            # print(obs['inventory'])
            
            # print(cum_rewards[position])
            # Display info stuff!
            controls_viewer.render(obs,rew, done,action, position, len(data_frames))
            if QUIT in controls_viewer.keys_down:
                leave = True
            elif FORWARD in controls_viewer.keys_down:
                new_position = min(position + speed, file_len -1)
            elif  BACK in controls_viewer.keys_down:
                new_position = max(position -speed, 0)
            elif FRAME_UP in controls_viewer.keys_down:
                new_position = min(position + 1, len(data_frames)-1)
                controls_viewer.keys_down.remove(FRAME_UP)
            elif FRAME_DOWN in controls_viewer.keys_down:
                new_position = max(position - 1, 0)
                controls_viewer.keys_down.remove(FRAME_DOWN)
            elif SPEED_UP in controls_viewer.keys_down:
                speed*=2
                controls_viewer.keys_down.remove(SPEED_UP)
            elif SLOWE_DOWN in controls_viewer.keys_down:
                speed = max(1, speed //2)
                controls_viewer.keys_down.remove(SLOWE_DOWN)

            time.sleep(0.05)

    main(parse_args())
