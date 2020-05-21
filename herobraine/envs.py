from herobraine.env_specs.navigate_specs import *
from herobraine.env_specs.treechop_specs import *
from herobraine.env_specs.obtain_diamond_specs import *
from herobraine.env_specs.obtain_iron_pickaxe_specs import *
from herobraine.env_specs.survival_specs import *
from herobraine.env_specs.env_spec import EnvSpec

MINERL_TREECHOP_V0 = Treechop()
MINERL_NAVIGATE_V0 = Navigate(dense=False, extreme=False)
MINERL_NAVIGATE_EXTREME_V0 =  Navigate(dense=False, extreme=True)
MINERL_NAVIGATE_DENSE_V0 = Navigate(dense=True, extreme=False)
MINERL_NAVIGATE_DENSE_EXTREME_V0 =  Navigate(dense=True, extreme=True)


MINERL_TREECHOP_VECTOR = VecWrapper(MINERL_TREECHOP_V0, common_envs=[MINERL_OBTAIN_DIAMOND_V0])


ENVS = [env for env in locals() if isinstance(env, EnvSpec)]

for env in ENVS:
    env.register()