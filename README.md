# MineRL

Python package providing easy to use gym environments and a simple data api for the MineRLv0 dataset. 

**To [get started please read the docs here](http://minerl.io/docs/)!**

## Installation

With JDK-8 installed run this command
```
pip3 install --upgrade minerl
```

## Basic Usage
```
import minerl
import gym
env = gym.make('MineRLNavigateDense-v0')


obs, _ = env.reset()

while not done:
    action = env.action_space.random() 
 
    # One can also take a no_op action with
    # action =env.action_space.noop()
    
 
    obs, reward, done, info = env.step(
        action)

```

## MineRL Competition
If you're here for the MineRL competition. Please check [the main competition website here](https://www.aicrowd.com/challenges/neurips-2019-minerl-competition).
