# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

from collections import OrderedDict, MutableMapping

from minerl.herobraine.env_spec import EnvSpec
from minerl.herobraine.wrappers.wrapper import EnvWrapper


# def foo():
#     return ss = {
#             o.to_string(): o.space for o in self.observables if not hasattr(o, 'hand')
#         }
#         try:
#             if [o.space for o in self.observables if hasattr(o, 'hand')]:
#                 ss.update({
#                     'equipped_items': spaces.Dict({
#                         'mainhand': spaces.Dict({
#                             o.to_string(): o.space for o in self.observables if hasattr(o, 'hand')
#                         })
#                     })
#                 })
#         except Exception as e:
#             print(e)
#             pass


def flatten(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


class Compat_v0(EnvWrapper):
    def _update_name(self, name: str) -> str:
        return self.name

    def _wrap_observation(self, obs: OrderedDict) -> OrderedDict:
        for key, hdl in obs:
            if '.' in key:
                obs['key'] = flatten(obs['key'])
        return obs

    def _wrap_action(self, act: OrderedDict) -> OrderedDict:
        for key, hdl in act:
            if '.' in key:
                act['key'] = flatten(act['key'])
        return act

    def _unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        for key, hdl in obs:
            if '.' in key:
                obs['key'] = flatten(obs['key'])
        return obs

    def _unwrap_action(self, act: OrderedDict) -> OrderedDict:
        for key, hdl in act:
            if '.' in key:
                act['key'] = flatten(act['key'])
        return act

    def __init__(self, env_to_wrap: EnvSpec, name: str):
        super().__init__(env_to_wrap)
        self.name = name
        pass
