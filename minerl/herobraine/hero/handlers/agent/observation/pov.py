
import logging

import jinja2
from minerl.herobraine.hero.handlers.translation import KeymapTranslationHandler
from minerl.herobraine.hero import spaces
from typing import Tuple


class POVObservation(KeymapTranslationHandler):
    """
    Handles POV observations.
    """

    def to_string(self):
        return 'pov'

    def xml_template(self) -> jinja2.Template:
        return jinja2.Template("""
            <VideoProducer 
                want_depth="{{ str(self.include_depth).lower() }}">
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
        self.video_height = video_resolution[0]
        self.video_width = video_resolution[1]

        super().__init__(
            hero_keys=["pov"], 
            univ_keys=["pov"], space=space)

    
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

    
