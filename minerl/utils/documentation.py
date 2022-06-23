import json

import gym
from typing import Union

from minerl.herobraine.env_spec import EnvSpec
from minerl.herobraine.env_specs import basalt_specs
from minerl.herobraine.hero.handlers import util


def _gym_space_to_dict(space: Union[dict, gym.Space]) -> dict:
    if isinstance(space, gym.spaces.Dict):
        dct = {}
        for k in space.spaces:
            dct[k] = _gym_space_to_dict(space.spaces[k])
        return dct
    else:
        return space


def _format_dict(arg: dict) -> str:
    arg = {":ref:`{} <{}>`".format(k, k): arg[k] for k in arg}
    json_obj = json.dumps(arg, sort_keys=True, indent=8, default=lambda o: str(o))
    json_obj = json_obj[:-1] + "    })"
    return f'.. parsed-literal:: \n\n    Dict({json_obj}\n\n\n'


def print_env_spec_sphinx(env_spec: EnvSpec) -> None:
    env = env_spec()
    env_name = env.name
    print("_" * len(env_name))
    print(f"{env_name}")
    print("_" * len(env_name))
    print(env.get_docstring())

    if hasattr(env, "inventory"):
        print("..................")
        print("Starting Inventory")
        print("..................")
        starting_inv_canonical = {}
        for stack in env.inventory:
            item_id = util.encode_item_with_metadata(stack["type"], stack.get("metadata"))
            starting_inv_canonical[item_id] = stack["quantity"]
        print(_format_dict(starting_inv_canonical))

    print(".....")
    print("Usage")
    print(".....")

    usage_str = f'''.. code-block:: python
        env = gym.make("{env_name}")  # A {env_name} env
    '''
    print(usage_str)