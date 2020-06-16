import minerl
import numpy as np

e = minerl.herobraine.envs.MINERL_OBTAIN_DIAMOND_DENSE_OBF_V0

vector_env = e.env_to_wrap
orig_env = vector_env.env_to_wrap
# u = vector_env.action_space.sample(32)['vector']
# print(vector_env.common_action_space.unmap(u))
# # print(u, vector_env.common_action_space.flat_map(vector_env.common_action_space.unmap(u)))
# # print( e.env_to_wrap.action_space.sample()['vector'])
# d = e.ac_dec(e.ac_enc(u))
# print(vector_env.common_action_space.unmap(d))


# Here's the issue. When we train with the uniform embedding, we fail to minimize the recoding error.
# We should train using a mixture of all three data types, as well as the recode error.

u = orig_env.action_space.no_op()
u['craft'] = 'torch'
print(u)
print(e.wrap_action(u))
print(e.unwrap_action(e.wrap_action(u)))



# u = orig_env.observation_space.no_op()
# u['equipped_items.mainhand.type'] = 'iron_pickaxe'
# print(u)
# # print(e.wrap_observation(u))
# print(e.unwrap_observation(e.wrap_observation(u)))