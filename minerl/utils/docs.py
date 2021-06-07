import json

import gym

from minerl.herobraine import envs
from minerl.herobraine.env_spec import EnvSpec


def _prep_space(space: gym.Space) -> gym.Space:
    if isinstance(space, gym.spaces.Dict):
        dct = {}
        for k in space.spaces:
            dct[k] = _prep_space(space.spaces[k])
        return dct
    else:
        return space


def _print_json(arg: dict) -> None:
    arg = {":ref:`{} <{}>`".format(k, k): arg[k] for k in arg}
    json_obj = json.dumps(arg, sort_keys=True, indent=8, default=lambda o: str(o))
    json_obj = json_obj[:-1] + "    })"
    print('.. parsed-literal:: \n\n    Dict(%s\n\n\n' % json_obj)


BASIC_ENV_SPECS = [
    envs.MINERL_TREECHOP_V0,
    envs.MINERL_NAVIGATE_V0,
    envs.MINERL_NAVIGATE_DENSE_V0,
    envs.MINERL_NAVIGATE_EXTREME_V0,
    envs.MINERL_NAVIGATE_DENSE_EXTREME_V0,
    envs.MINERL_OBTAIN_DIAMOND_V0,
    envs.MINERL_OBTAIN_DIAMOND_DENSE_V0,
    envs.MINERL_OBTAIN_IRON_PICKAXE_V0,
    envs.MINERL_OBTAIN_IRON_PICKAXE_DENSE_V0,
]

COMPETITION_ENV_SPECS = [
    envs.MINERL_TREECHOP_OBF_V0,
    envs.MINERL_NAVIGATE_OBF_V0,
    envs.MINERL_NAVIGATE_DENSE_OBF_V0,
    envs.MINERL_NAVIGATE_EXTREME_OBF_V0,
    envs.MINERL_NAVIGATE_DENSE_EXTREME_OBF_V0,
    envs.MINERL_OBTAIN_DIAMOND_OBF_V0,
    envs.MINERL_OBTAIN_DIAMOND_DENSE_OBF_V0,
    envs.MINERL_OBTAIN_IRON_PICKAXE_OBF_V0,
    envs.MINERL_OBTAIN_IRON_PICKAXE_DENSE_OBF_V0,
]


def print_actions_for_id(env_spec: EnvSpec) -> None:
    print("______________")
    print(f"{env_spec.name}")
    print("______________")
    print(env_spec.get_docstring())

    action_space = _prep_space(env_spec.action_space)
    state_space = _prep_space(env_spec.observation_space)

    print(".......")
    print("Observation Space")
    print(".......")
    _print_json(state_space)

    print(".......")
    print("Action Space")
    print(".......")
    _print_json(action_space)

    print(".......")
    print("Usage")
    print(".......")

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
