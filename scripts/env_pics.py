"""
Sanity check script that makes screenshots for every BASALT env and for several seeds.
"""
import pathlib

import gym
from matplotlib import pyplot as plt
import minerl  # Registers envs


OUTPUT_ROOT = pathlib.Path("logs", "env_imgs")  # Images are saved here
N_SEEDS = 10  # The number of seeds to try for each environment.
N_TRYS = 1  # Set greater than 1 to see if seeds replicate
STEP_RANGES = [0]  # For each step number, take that many noop actions and then take a picture.

ENV_NAMES = [
    "MineRLBasaltFindCave-v0",
    "MineRLBasaltMakeWaterfall-v0",
    "MineRLBasaltCreateVillageAnimalPen-v0",
    "MineRLBasaltBuildVillageHouse-v0",
]


def psuedo_main():
    for env_name in ENV_NAMES:
        output_dir = OUTPUT_ROOT / env_name
        for seed in range(N_SEEDS):
            for trie in range(N_TRYS):
                with gym.make(env_name) as env:
                    env.seed(seed)
                    obs = env.reset()
                    for n_steps in range(max(STEP_RANGES) + 1):
                        if n_steps in STEP_RANGES:
                            save_path = output_dir / f"seed{seed:02d}_{n_steps:02d}_{trie:02d}.png"
                            save_path.parent.mkdir(parents=True, exist_ok=True)
                            # plt.imshow(obs['pov'])
                            plt.imsave(save_path, obs['pov'])
                            print(f"Saved a screenshot to {str(save_path)}")


if __name__ == "__main__":
    psuedo_main()
