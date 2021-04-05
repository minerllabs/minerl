# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton


import logging

import jinja2
from minerl.herobraine.hero.handlers.translation import KeymapTranslationHandler
from minerl.herobraine.hero import spaces
from typing import Tuple
import numpy as np


class POVObservation(KeymapTranslationHandler):
    """
    Handles POV observations.
    """

    def to_string(self):
        return 'pov'

    def xml_template(self) -> str:
        return str("""
            <VideoProducer 
                want_depth="{{ include_depth | string | lower }}">
                <Width>{{ video_width }} </Width>
                <Height>{{ video_height }}</Height>
            </VideoProducer>""")

    def __init__(self, video_resolution: Tuple[int, int], include_depth: bool = False):
        self.include_depth = include_depth
        self.video_resolution = video_resolution
        space = None
        if include_depth:
            space = spaces.Box(0, 255, list(video_resolution)[::-1] + [4], dtype=np.uint8)
            self.video_depth = 4

        else:
            space = spaces.Box(0, 255, list(video_resolution)[::-1] + [3], dtype=np.uint8)
            self.video_depth = 3

        # TODO (R): FIGURE THIS THE FUCK OUT & Document it.
        self.video_height = video_resolution[1]
        self.video_width = video_resolution[0]

        super().__init__(
            hero_keys=["pov"],
            univ_keys=["pov"], space=space)

    def from_hero(self, obs):
        byte_array = super().from_hero(obs)
        pov = np.frombuffer(byte_array, dtype=np.uint8)

        if pov is None or len(pov) == 0:
            pov = np.zeros((self.video_height, self.video_width, self.video_depth), dtype=np.uint8)
        else:
            pov = pov.reshape((self.video_height, self.video_width, self.video_depth))[::-1, :, :]

        return pov

    def __or__(self, other):
        """
        Combines two POV observations into one. If all of the properties match return self
        otherwise raise an exception.
        """
        if isinstance(other, POVObservation) and self.include_depth == other.include_depth and \
                self.video_resolution == other.video_resolution:
            return POVObservation(self.video_resolution, include_depth=self.include_depth)
        else:
            raise ValueError("Incompatible observables!")

class VoxelObservation(KeymapTranslationHandler):
    """
    Handles voxel observations.
    """

    def to_hero(self, x) -> str:
        pass

    def to_string(self):
        return 'voxels'

    def xml_template(self) -> str:
        return str("""
            <ObservationFromGrid>                      
                <Grid name="voxels">                        
                    <min x="{{xmin}}" y="{{ymin}}" z="{{zmin}}"/>                        
                    <max x="{{xmax}}" y="{{ymax}}" z="{{zmax}}"/>                      
                </Grid>                  
            </ObservationFromGrid>""")

    def __init__(self, limits=((-3,3), (-1,3), (-3,3))):
        self.xmin = limits[0][0]
        self.ymin = limits[1][0]
        self.zmin = limits[2][0]
        self.xmax = limits[0][1]
        self.ymax = limits[1][1]
        self.zmax = limits[2][1]
        self.grid_size = [1 + b - a for a, b in limits]

        space = spaces.Box(0, 1<<22, self.grid_size, dtype=np.uint32)

        super().__init__(
            hero_keys=["voxels"],
            univ_keys=["voxels"], space=space)

    def from_hero(self, obs):
        voxels_arr = super().from_hero(obs, dtype=np.int32)

        voxels = voxels_arr.reshape(self.grid_size)

        return voxels

    def __or__(self, other):
        """
        Combines two voxel observations into one. If all of the properties match return self
        otherwise raise an exception.
        """
        if isinstance(other, VoxelObservation) and self.grid_min == other.grid_min and \
                self.grid_max == other.grid_max:
            return self
        else:
            raise ValueError("Incompatible observables!")

class RichLidarObservation(KeymapTranslationHandler):
    """
    Handles rich LIDAR observations.
    """

    def to_hero(self, x) -> str:
        pass

    def to_string(self):
        return 'rays'

    def xml_template(self) -> str:
        return str("""
            <ObservationFromRichLidar>
                {% for ray in rays %}
                    <RayOffset pitch="{{ray[0]}}" yaw="{{ray[1]}}" distance="{{ray[2]}}"/>
                {% endfor %}
            </ObservationFromRichLidar>
        """)

    def __init__(self, rays=None):
        # Note rays use [pitch, yaw, distance]:
        # The pitch (in radians) is relative to lookVec
        # The yaw (in radians) is relative to lookVec
        # The distance (in meters) is the maximum distance for the ray from eyePos

        if rays is None:
            rays = [(0.0, 0.0, 10.0),]
        self.rays = rays
        self.num_rays = len(rays)
        self.num_components = 12 # TODO get this from java
        self.shape = (self.num_rays, self.num_components)

        space = spaces.Box(0, 1 << 31, self.shape, dtype=np.uint32)

        super().__init__(
            hero_keys=["rays"],
            univ_keys=["rays"],
            space=space,
            xml_keys={"rays": self.rays})

    def from_hero(self, obs):
        raw_rays = super().from_hero(obs, dtype=np.int32)

        rays = raw_rays.reshape(self.shape)

        return rays

    def __or__(self, other):
        """
        Combines two rich lidar observations into one.
        """
        if isinstance(other, RichLidarObservation):
            all_rays = self.rays + other.rays
            return RichLidarObservation(rays=all_rays)
        else:
            raise ValueError("Incompatible observables!")