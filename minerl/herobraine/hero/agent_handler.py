from abc import ABC
from collections.abc import MutableMapping
from typing import Iterator, Any, Tuple
from xml.etree.ElementTree import Element

import gym

from minerl.herobraine.hero.spaces import MineRLSpace


class AgentHandler(ABC):
    """
    An agent handler to be added to the mission XML.
    This is useful as it defines basically all of the interfaces
    between universal action format, hero (malmo), and herobriane (ML stuff).
    """

    def __init__(self, space: MineRLSpace):
        self.space = space

    def add_to_mission_spec(self, mission_spec):
        pass

    def to_string(self) -> str:
        raise NotImplementedError()

    def add_to_mission_xml(self, etree: Element, namespace: str):
        pass

    def from_hero(self, obs_dict):
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

    def from_universal(self, x):
        """sure
        Converts a universal representation of the handler (e.g. unviersal action/observation)
        """
        raise NotImplementedError()


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



class HandlerCollection(MutableMapping):
    """
    A mapping of agent handlers and various forms thereof
    whcih allows access by class type or by instance. For example,
    ```
    hand1 = ContinuousMovementAction()
    hand2 = POVObservation(192)

    hcol = HandlerCollection()
    hcol[hand1] = 5
    hcol[hand2] = 15

    # Normal access
    print(hcol[hand1]) # 5

    # Type access
    print(hcol[ContinuousMovementAction]) # 5
    ```

    If multiple instances of the type being accessed exist
    the operation is applied uniformly
    ```
    hcol = HandlerCollection({
        ContinuousMovementAction(): 15,
        ContinuousMovementAction(): 45
        POVObservation(123,1643, depth=False): [255,255,0,0,0,255,...]
    })

    hcol[ContinuousMovementAction] = 17
    hcol # {
         #       ContinuousMovementAction object: 17,
         #       ContinuousMovementAction object: 17, ....}

    ```
    """

    def __init__(self, *args, **kwargs):
        self.__store = dict(*args, **kwargs)

    def __setitem__(self, k: Any, v: Any) -> None:
        if isinstance(k, type):
            if not k in self:
                raise KeyError('Cannot set by type {} because no instance'
                               ' thereof exists in the collection.'.format(k))
            else:
                valid_keys = [skey for skey in self.__store if isinstance(skey, k)]
                for sk in valid_keys:
                    self.__store[sk] = v
        else:
            self.__store[k] = v

    def __delitem__(self, k) -> None:
        if isinstance(k, type):
            valid_keys = [skey for skey in self.__store if isinstance(skey, k)]
            for sk in valid_keys:
                del self.__store[sk]
        else:
            del self.__store[k]

    def __getitem__(self, k: Any) -> Any:
        if isinstance(k, type):
            valid_keys = [skey for skey in self.__store if isinstance(skey, k)]
            if len(valid_keys) == 0:
                raise KeyError("No object with type {} found.".format(k))
            items = [self.__store[skey] for skey in valid_keys]
            if len(items) == 1:
                return items[0]
            else:
                return items
        else:
            return self.__store[k]

    def item_from_handler(self, k: type) -> Tuple[Any, Any]:
        valid_keys = [skey for skey in self.__store if isinstance(skey, k)]
        return valid_keys[0], self.__store[valid_keys[0]]

    def __repr__(self) -> str:
        return self.__store.__repr__()

    def __len__(self) -> int:
        return len(self.__store.keys())

    def __iter__(self) -> Iterator[Any]:
        return iter(self.__store)
