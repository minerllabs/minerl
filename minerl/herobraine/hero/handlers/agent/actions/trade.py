# Copyright (c) 2020 All Rights Reserved
# Author: Adrien Ecoffet

from minerl.herobraine.hero.handlers.agent.action import Action
import jinja2
import minerl.herobraine.hero.spaces as spaces
import numpy as np
from minerl.herobraine.hero.mc import ALL_ITEMS


class TradeNearby(Action):
    """
    An action handler for trading between agents
    """

    _command = "trade"

    def __init__(self):
        super().__init__(
            self.command, spaces.Dict(
                {
                    "target": spaces.Discrete(2),
                    "trades": spaces.Dict(
                        {k: spaces.Box(low=1000, high=-1000, shape=(), dtype=np.int32) for k in ALL_ITEMS}
                    )
                },
            )
        )

    def to_string(self):
        return "trade"

    def xml_template(self) -> str:
        return str("<TradeCommands/>")

    def from_universal(self, obs):
        raise NotImplementedError()

    def to_hero(self, x):
        """
        Returns a command string for the multi command action.
        :param x:
        :return:
        """
        target = x["target"]
        if isinstance(target, int):
            target = f"MineRLAgent{target}"
        trade_str = " ".join(f"{k}:{v}" for k, v in x.get("trades", {}).items())
        return f"{self.command} {target} {trade_str}"

