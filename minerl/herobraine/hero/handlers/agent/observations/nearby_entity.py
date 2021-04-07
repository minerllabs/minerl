# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import logging
import numpy as np

import minerl.herobraine.hero.mc as mc
from minerl.herobraine.hero.handlers.translation import TranslationHandler, TranslationHandlerGroup
from minerl.herobraine.hero import spaces


class NearbyEntityObservation(TranslationHandlerGroup):
    """
    List of nearby entities
    """
    def to_string(self):
        return 'entities'

    def xml_template(self) -> str:
        return str(
            f"""<ObservationFromNearbyEntities>
    <Range name="entities" xrange="{self.x_range}" yrange="{self.y_range}" zrange="{self.z_range}"/>
</ObservationFromNearbyEntities>""")

    logger = logging.getLogger(__name__ + ".NearbyEntityObservation")

    def __init__(self, item_list, max_entities=10, x_range=5.0, y_range=5.0, z_range=5.0):
        self.item_list = item_list
        self.x_range, self.y_range, self.z_range = x_range, y_range, z_range
        self.max_entities = max_entities

        handlers = [
            EntityObservation(self.item_list, i) for i in range(max_entities)
        ]
        super().__init__(handlers)

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and other.x_range == self.x_range
            and other.y_range == self.y_range
            and other.z_range == self.z_range
            and other.max_entities == self.max_entities
            and other.item_list == self.item_list
        )

    def __or__(self, other):
        return NearbyEntityObservation(
            item_list=list(set(self.item_list) | set(other.item_list)),
            max_entities=self.max_entities,
            x_range=self.x_range,
            y_range=self.y_range,
            z_range=self.z_range,
        )


class EntityObservation(TranslationHandler):
    """
    List of nearby entities
    """
    def to_string(self):
        return 'entities'

    logger = logging.getLogger(__name__ + ".EntityObservation")

    def __init__(self, item_list, idx, _other='other'):
        self.items = sorted(item_list)
        self.idx = idx
        self._other = _other
        if self._other not in self.items:
            self.items.append(self._other)

        # TODO this needs to be a tuple
        self.space = spaces.Dict(spaces={
            "type": spaces.Enum(*self.items),
            "player_delta": spaces.Box(low=-5, high=5, shape=(3,), dtype=np.float32),
            "motion": spaces.Box(low=-5, high=5, shape=(3,), dtype=np.float32),
            "quantity": spaces.Box(low=0, high=2304, shape=(), dtype=np.int),
            "valid": spaces.Box(low=0, high=1, shape=(), dtype=np.int),
        })
        super().__init__(self.space)

    def __or__(self, other):
        if isinstance(other, EntityObservation):
            return EntityObservation(list(set(self.items + other.items)), self.idx or other.idx)
        else:
            raise TypeError("Operands have to be of type EntityObservation")

    def __eq__(self, other):
        return self.items == other.items and self.idx == other.idx

    def from_hero(self, obs):
        """
        Example input:

        [{'yaw': -54.0,
          'x': -80.95586051126129,
          'y': 80.17675927506424,
          'z': 191.36564594298798,
          'pitch': 6.0,
          'id': 'dbdbc990-b55b-31ee-a5e0-8b26ffa9a1ae',
          'motionX': 0.07562785839444941,
          'motionY': -0.15233518685055708,
          'motionZ': 0.03299904674152276,
          'life': 16.0,
          'name': 'MineRLAgent1',
          'lookVecDotProduct': 1.0,
          'playerDeltaX': 0.0,
          'playerDeltaY': 0.0,
          'playerDeltaZ': 0.0},
         {'yaw': 146.25,
          'x': -80.96685039870985,
          'y': 77.70749819972261,
          'z': 194.81005356662737,
          'pitch': 0.0,
          'id': '79631974-1b7b-4bab-b221-9abd25f9d6d8',
          'motionX': 0.07181885258824576,
          'motionY': -0.48115283512326734,
          'motionZ': 0.19435422823880838,
          'quantity': 1,
          'name': 'light_weighted_pressure_plate',
          'lookVecDotProduct': -1.0,
          'playerDeltaX': -0.010989887448559443,
          'playerDeltaY': -2.4692610753416346,
          'playerDeltaZ': 3.4444076236393926}]
        """

        out = self.space.no_op()
        valid_entity = False
        if self.idx < len(obs["entities"]):
            entity_list = sorted(obs["entities"], key=lambda x: x["playerDeltaX"] ** 2 + x["playerDeltaY"] ** 2 + x["playerDeltaZ"] ** 2)
            entity = entity_list[self.idx]
            # hide things that are behind us
            # TODO make this respect occlusions.
            if entity["lookVecDotProduct"] >= 0:
                valid_entity = True
                out["type"] = entity["name"] if entity["name"] in self.items else self._other
                out["player_delta"] = (entity["playerDeltaX"], entity["playerDeltaY"], entity["playerDeltaZ"])
                out["motion"] = (entity["motionX"], entity["motionY"], entity["motionZ"])
                out["quantity"] = entity.get("quantity", 0)
                out["life"] = entity.get("life", 0)
                out["valid"] = 1

        if not valid_entity:
            out["type"] = self._other
            out["player_delta"] = 0, 0, 0
            out["motion"] = 0, 0, 0
            out["quantity"] = 0
            out["life"] = 0
            out["valid"] = 0
        return out
