"""Solution code for the mlg_wb gym"""

__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

# initialization steps
import gym
from mlg_wb_specs import MLGWB

# In order to use the environment as a gym you need to register it with gym
abs_MLG = MLGWB()
abs_MLG.register()
env = gym.make("MLGWB-v0")
obs  = env.reset()

# move back and look down
for i in range(21):
    action = env.action_space.noop()
    action["back"] = 1
    obs, reward, done, info = env.step(action)
    env.render()
    
for i in range(20):
    action = env.action_space.noop()
    action["back"] = 0
    action["camera"] = [5, 0]
    obs, reward, done, info = env.step(action)
    env.render()

while obs["location_stats"]["ypos"] > 7.5:
    action = env.action_space.noop()
    obs, reward, done, info = env.step(action)
    env.render()

# place the water bucket
action = env.action_space.noop()
action["use"] = 1
obs, reward, done, info = env.step(action)
env.render()

# noop
action = env.action_space.noop()
print(action, obs["life_stats"])
obs, reward, done, info = env.step(action)
env.render()

# pick the water back up
action = env.action_space.noop()
action["use"] = 1
obs, reward, done, info = env.step(action)
env.render()

# equip the pickaxe
action = env.action_space.noop()
action["equip"] = "diamond_pickaxe"
obs, reward, done, info = env.step(action)
env.render()

# mine the gold block
while not done:
    action = env.action_space.noop()
    action["attack"] = 1
    obs, reward, done, info = env.step(action)
    env.render()
