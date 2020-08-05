
import logging

import numpy as np
from minerl.herobraine.hero.spaces import MineRLSpace
import minerl.herobraine.hero.spaces as spaces
from typing import List, Any
import typing
from minerl.herobraine.hero.handler import Handler


class TranslationHandler(Handler):
    """
    An agent handler to be added to the mission XML.
    This is useful as it defines basically all of the interfaces
    between universal action format, hero (malmo), and herobriane (ML stuff).
    """

    def __init__(self, space: MineRLSpace, **other_kwargs):
        self.space = space


    def from_hero(self, x : typing.Dict[str, Any]) :
        """
        Converts a "hero" representation of an instance of this handler
        to a member of the space.
        """
        raise NotImplementedError()

    def to_hero(self, x) -> str:
        """
        Takes an instance of the handler, x \in self.space, and maps it to
        the "hero" representation thereof.
        """
        raise NotImplementedError()

    def from_universal(self, x : typing.Dict[str, Any]):
        """sure
        Converts a universal representation of the handler (e.g. unviersal action/observation)
        """
        raise NotImplementedError()


# TODO: ONLY WORKS FOR OBSERVATIONS.
# TODO: Consider moving this to observations.
class KeymapTranslationHandler(TranslationHandler):
    def __init__(self, 
        hero_keys: typing.List[str], 
        univ_keys: typing.List[str], 
        space: MineRLSpace, default_if_missing=None,
        to_string : str = None):
        """
        Wrapper for simple observations which just remaps keys.
        :param keys: list of nested dictionary keys from the root of the observation dict
        :param space: gym space corresponding to the shape of the returned value
        :param default_if_missing: value for handler to take if missing in the observation dict
        """
        super().__init__(space)
        self.hero_keys = hero_keys
        self.univ_keys = univ_keys
        self.default_if_missing = default_if_missing
        self.logger = logging.getLogger(f'{__name__}.{self.to_string()}')
        self._to_string = to_string if to_string else hero_keys[-1]

    def walk_dict(self, d, keys):
        for key in keys:
            if key in d:
                d = d[key]
            else:
                if self.default_if_missing is not None:
                    self.logger.error(f"No {keys[-1]} observation! Yielding default value "
                                      f"{self.default_if_missing} for {'/'.join(keys)}")
                    return np.array(self.default_if_missing)
                else:
                    raise KeyError()
        return np.array(d)

    def to_hero(self, x) -> str:
        """What does it mean to do a keymap translation here?
        Since hero sends things as commands perhaps we could generalize
        this beyond observations.
        """
        raise NotImplementedError()

    def from_hero(self, hero_dict):
        return self.walk_dict(hero_dict, self.hero_keys)

    def from_universal(self, univ_dict):
        return self.walk_dict(univ_dict, self.univ_keys)
    
    def to_string(self) -> str:
        return self._to_string
    
class TranslationHandlerGroup(TranslationHandler):
    """Combines several space handlers into a single handler group.
    """
    def __init__(self, handlers : List[TranslationHandler]):
        self.handler_dict = {h.to_string() : h for h in handlers}
        super(TranslationHandlerGroup, self).__init__(
            spaces.Dict(self.handler_dict)
        )

    def to_hero(self, x : typing.Dict[str, Any]) -> str:
        """Produces a string from an object X contained in self.space
        into a string by calling all of the corresponding
        to_hero methods and joining them with new lines
        """

        return  "\n".join(
            [self.handler_dict[s].to_hero(x[s]) for s in self.handler_dict])

    def from_hero(self, x : typing.Dict[str, Any]) -> typing.Dict[str, Any]:
        """Applies the constituent from_hero methods on the object X 
           and builds a dictionary with keys corresponding to the constituent 
           handlers applied."""

        return  {
            s : self.handler_dict[s].from_hero(x)
            for s in self.handler_dict
        }

    def from_universal(self, x: typing.Dict[str, Any]) -> typing.Dict[str, Any]:
        """Performs the same operation as from_hero except with from_universal.
        """
        return  {
            s : self.handler_dict[s].from_universal(x)
            for s in self.handler_dict
        }

    def __eq__(self, other):
        return (
            super().__eq__(other) 
            and isinstance(other, TranslationHandlerGroup)
            and self.handler_dict == other.handler_dict
        )

    def __or__(self, other):
        
        """Overloads | (binary or) operator. 
        Joins the two handler groups by matching all keys 
        and combining their translation dictionaries."""
        
        assert self.to_string() == other.to_string()
        assert set(self.handler_dict.keys()) == set(other.handler_dict.keys())
        return TranslationHandlerGroup(
            [self.handler_dict[k] | other.handler_dict[k] 
                for k in self.handler_dict.keys()]
        )







