import collections
import numpy as np
from functools import reduce

from typing import List, Tuple

from herobraine.hero import AgentHandler
from herobraine.hero.spaces import MineRLSpace, Box, Dict


def union_spaces(hdls_1 : List[AgentHandler], hdls_2 : List[AgentHandler]) -> List[MineRLSpace]:
    # Merge action/observation spaces from two environments
    hdls = hdls_1 + hdls_2
    hdl_dict = collections.defaultdict(list)
    _ = [hdl_dict[hdl.to_string()].append(hdl) for hdl in hdls]  # Join matching handlers
    merged_hdls = [reduce(lambda a, b: a | b, matching) for matching in hdl_dict.values()]

    return merged_hdls


def flatten_spaces(hdls : List[AgentHandler]) -> Tuple[list, List[Tuple[str, MineRLSpace]]]:
    return [hdl.space.flattened for hdl in hdls if hdl.space.is_flattenable()], [(hdl.to_string(), hdl.space) for hdl in hdls if not hdl.space.is_flattenable()]  # return [hdl.space.flattened for hdl in hdls if hdl.space.is_flattenable()], [hdl for hdl in hdls if not hdl.space.is_flattenable()]

