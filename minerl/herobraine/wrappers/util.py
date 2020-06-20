import collections
import numpy as np
from functools import reduce

from typing import List, Tuple

from minerl.herobraine.hero import AgentHandler
from minerl.herobraine.hero.spaces import Box, Dict, Enum, MineRLSpace


# TODO: Make a test.
# TODO: Refactor this. This iss unioning handlers, not sapces.
def union_spaces(hdls_1: List[AgentHandler], hdls_2: List[AgentHandler]) -> List[MineRLSpace]:
    # Merge action/observation spaces from two environments
    hdls = hdls_1 + hdls_2
    hdl_dict = collections.defaultdict(list)
    _ = [hdl_dict[hdl.to_string()].append(hdl) for hdl in hdls]  # Join matching handlers
    merged_hdls = [reduce(lambda a, b: a | b, matching) for matching in hdl_dict.values()]

    return merged_hdls



# TODO: make a test.
# TODO: Maybe this should be based on handlers as above.
# E.g. 1. Intersect the handlers
# E.g. 2. We then do best effort clipping for spaces space.intersect
# wg note: whenever you write isinstance for a bunch of classes 
# you are being a fucing idiot this is exactly why we have object 
# oriented programming.
def intersect_space(space, sample):
    if isinstance(space, Dict):
        new_sample = collections.OrderedDict()
        for key, value in space.spaces.items():
            new_sample[key] = intersect_space(value, sample[key])
        return new_sample
    elif isinstance(space, Enum):
        if sample not in space:
            return space.default    
        else:
            return sample
    else:
        # TODO: SUPPORT SPACE INTERSECTION.
        return sample


# TODO: make a test
def flatten_spaces(hdls: List[AgentHandler]) -> Tuple[list, List[Tuple[str, MineRLSpace]]]:
    return [hdl.space.flattened for hdl in hdls if hdl.space.is_flattenable()], \
           [(hdl.to_string(), hdl.space) for hdl in hdls if
            not hdl.space.is_flattenable()]
