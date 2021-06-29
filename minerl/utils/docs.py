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
    print("_" * len(env_spec.name))
    print(f"{env_spec.name}")
    print("_" * len(env_spec.name))
    print(env_spec.get_docstring())

    action_space = _gym_space_to_dict(env_spec.action_space)
    state_space = _gym_space_to_dict(env_spec.observation_space)

    print(".................")
    print("Observation Space")
    print(".................")
    print(_format_dict(state_space))

    print("............")
    print("Action Space")
    print("............")
    print(_format_dict(action_space))

    if isinstance(env_spec, basalt_specs.BasaltBaseEnvSpec):
        print("..................")
        print("Starting Inventory")
        print("..................")
        starting_inv_canonical = {}
        for stack in env_spec.inventory:
            item_id = util.encode_item_with_metadata(stack["type"], stack.get("metadata"))
            starting_inv_canonical[item_id] = stack["quantity"]
        print(_format_dict(starting_inv_canonical))

    print(".....")
    print("Usage")
    print(".....")

    usage_str = f'''.. code-block:: python

        import gym
        import minerl

        # Run a random agent through the environment
        env = gym.make("{env_spec.name}")  # A {env_spec.name} env

        obs = env.reset()
        done = False

        while not done:
            # Take a no-op through the environment.
            obs, rew, done, _ = env.step(env.action_space.noop())
            # Do something

        ######################################

        # Sample some data from the dataset!
        data = minerl.data.make("{env_spec.name}")

        # Iterate through a single epoch using sequences of at most 32 steps
        for obs, rew, done, act in data.batch_iter(num_epochs=1, batch_size=32):
            # Do something
    '''
    print(usage_str)
