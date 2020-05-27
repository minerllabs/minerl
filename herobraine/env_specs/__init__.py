import collections

from herobraine.env_spec import EnvSpec
from herobraine.env_specs.treechop_specs import Treechop
from herobraine.env_specs.navigate_specs import Navigate
from herobraine.env_specs.obtain_specs import ObtainDiamond, ObtainDiamondSurvival, ObtainIronPickaxe, Obtain
from herobraine.wrappers import Obfuscated, Vectorized

MINERL_TREECHOP_V0 = Treechop()

MINERL_NAVIGATE_V0 = Navigate(dense=False, extreme=False)
MINERL_NAVIGATE_EXTREME_V0 = Navigate(dense=False, extreme=True)
MINERL_NAVIGATE_DENSE_V0 = Navigate(dense=True, extreme=False)
MINERL_NAVIGATE_DENSE_EXTREME_V0 = Navigate(dense=True, extreme=True)

MINERL_OBTAIN_DIAMOND_V0 = ObtainDiamond(dense=False)
MINERL_OBTAIN_DIAMOND_DENSE_V0 = ObtainDiamond(dense=True)

MINERL_OBTAIN_IRON_PICKAXE_V0 = ObtainIronPickaxe(dense=False)
MINERL_OBTAIN_IRON_PICKAXE_DENSE_V0 = ObtainIronPickaxe(dense=True)

# # Survival envs
# MINERL_OBTAIN_DIAMOND_SURVIVAL_V0 = ObtainDiamondSurvival(dense=False)

# # prototype envs
# # TODO: Actually make these work and correct, it'll be good to release these.
# MINERL_OBTAIN_MEAT_V0 = Obtain(target_item='meat', dense=False, reward_schedule={
#     'beef': 1,
#     'mutton': 1,
#     'porkchop': 1,
#     'chicken': 1,
#     'cooked_beef': 10,
#     'cooked_mutton': 10,
#     'cooked_porkchop': 10,
#     'cooked_chicken': 10,
# })
# MINERL_OBTAIN_BED_V0 = Obtain(target_item='bed', dense=False, reward_schedule=None)


common_envs = [MINERL_OBTAIN_DIAMOND_V0, MINERL_TREECHOP_V0, MINERL_NAVIGATE_V0, MINERL_OBTAIN_IRON_PICKAXE_V0]

# Obfuscated environments.
MINERL_TREECHOP_OBF_V0 = Obfuscated(Vectorized(MINERL_TREECHOP_V0, common_envs=common_envs))

MINERL_NAVIGATE_OBF_V0 = Obfuscated(Vectorized(MINERL_NAVIGATE_V0, common_envs=common_envs))
MINERL_NAVIGATE_EXTREME_OBF_V0 = Obfuscated(Vectorized(MINERL_NAVIGATE_EXTREME_V0, common_envs=common_envs))
MINERL_NAVIGATE_DENSE_OBF_V0 = Obfuscated(Vectorized(MINERL_NAVIGATE_DENSE_V0, common_envs=common_envs))
MINERL_NAVIGATE_DENSE_EXTREME_OBF_V0 = Obfuscated(Vectorized(MINERL_NAVIGATE_DENSE_EXTREME_V0, common_envs=common_envs))

MINERL_OBTAIN_DIAMOND_OBF_V0 = Obfuscated(Vectorized(MINERL_OBTAIN_DIAMOND_V0, common_envs=common_envs))
MINERL_OBTAIN_DIAMOND_DENSE_OBF_V0 = Obfuscated(Vectorized(MINERL_OBTAIN_DIAMOND_DENSE_V0, common_envs=common_envs))

MINERL_OBTAIN_IRON_PICKAXE_OBF_V0 = Obfuscated(Vectorized(MINERL_OBTAIN_IRON_PICKAXE_V0, common_envs=common_envs))
MINERL_OBTAIN_IRON_PICKAXE_DENSE_OBF_V0 = Obfuscated(
    Vectorized(MINERL_OBTAIN_IRON_PICKAXE_DENSE_V0, common_envs=common_envs))

ENVS = [env for env in locals().values() if isinstance(env, EnvSpec)]

# Register the envs.
for env in ENVS:
    env.register()
