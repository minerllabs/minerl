from abc import ABC, abstractmethod
from collections.abc import MutableMapping
from typing import Dict, Iterator, Any, List, Tuple
import typing
from xml.etree.ElementTree import Element

import gym
import jinja2

from minerl.herobraine.hero.spaces import MineRLSpace, spaces


class Handler(ABC):
    """Defines the minimal interface for a MineRL handler.

    At their core, handlers should specify unique identifiers
    and a method for producing XML to be given in a mission XML.
    """

    @abstractmethod
    def to_string(self) -> str:
        """The unique identifier for the agent handler.
        This is used for constructing aciton/observation spaces
        and unioning different env specifications.
        """
        raise NotImplementedError()

    @abstractmethod
    def xml_template(self) -> jinja2.Template:
        """Generates an XML representation of the handler.

        This XML representaiton is templated via Jinja2 and
        has access to all of the member variables of the class.

        Note: This is not an abstract method so that 
        handlers without corresponding XML's can be combined in
        handler groups with group based XML implementations.
        """
        raise NotImplementedError()

    def xml(self) -> str:
        """Gets the XML representation of Handler by templating
        acccording to the xml_template class.


        Returns:
            str: the XML representation of the handler.
        """
        return self.xml_template().render(self.__dict__)

    
    def __or__(self, other):
        """
        Checks to see if self and other have the same to_string
        and if so returns self, otherwise raises an exception.
        """
        if self.to_string() == other.to_string():
            return self
        raise Exception("Incompatible handlers!")


    def __eq__(self, other):
        """
        Checks to see if self and other have the same to_string
        and if so returns self, otherwise raises an exception.
        """
        return self.to_string() == other.to_string()


