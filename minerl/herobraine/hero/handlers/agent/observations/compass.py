
"""
    Defines compass observations.
"""
import jinja2
import numpy as np

from minerl.herobraine.hero import spaces
from minerl.herobraine.hero.handlers.translation import KeymapTranslationHandler, TranslationHandlerGroup


__all__ = ['CompassObservation']
class CompassObservation(TranslationHandlerGroup):
    def to_string(self) -> str:
        return "compass"

    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<ObservationFromCompass/>"""
        ) 

    def __init__(self, angle=True, distance=False):
        """Initializes a compass observation. Forms

        Args:
            angle (bool, optional): Whether or not to include angle observation. Defaults to True.
            distance (bool, optional): Whether or not ot include distance observation. Defaults to False.
        """
        assert angle or distance, "Must observe either angle or distance"

        handlers = []

        if angle:
            handlers.append(
                _CompassAngleObservation()
            )
        if distance:
            handlers.append(
                KeymapTranslationHandler(
                    hero_keys=["distance"],
                    univ_keys=['compass']["distance"],
                    space=spaces.Box(low=0, high=128, shape=(1,), dtype=np.uint8))
            )

        super(CompassObservation, self).__init__(handlers=handlers)

class _CompassAngleObservation(KeymapTranslationHandler):
    """
    Handles compass angle observations (converting to the correct angle offset normalized.)
    """

    def __init__(self):
        super().__init__(
            hero_keys=["angle"],
            univ_keys=['compass',"angle"],
            space=spaces.Box(low=-180.0, high=180.0, shape=(), dtype=np.float32)
        )

    def from_universal(self, obs):
        y = np.array(((super().from_universal(obs) * 360.0 + 180) % 360.0) - 180)
        return y

    def from_hero(self, obs):
        return np.array((super.from_hero(obs) + 0.5) % 1.0)
