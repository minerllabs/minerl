# The [MineRL](http://minerl.io) Python Package 
[![Downloads](https://pepy.tech/badge/minerl)](https://pepy.tech/project/minerl) 

Python package providing easy to use gym environments and a simple data api for the MineRLv0 dataset. 

**To [get started please read the docs here](http://minerl.io/docs/)!**

## Installation

With JDK-8 installed run this command
```
pip3 install --upgrade minerl
```

## Basic Usage

Running an environment:
```python
import minerl
import gym
env = gym.make('MineRLNavigateDense-v0')


obs, _ = env.reset()

done = False
while not done:
    action = env.action_space.sample() 
 
    # One can also take a no_op action with
    # action =env.action_space.noop()
    
 
    obs, reward, done, info = env.step(
        action)

```

Sampling the dataset:

```python
import minerl

# YOU ONLY NEED TO DO THIS ONCE!
minerl.data.download('/your/local/path')

data = minerl.data.make('MineRLObtainDiamond-v0')

# Iterate through a single epoch gathering sequences of at most 32 steps
for obs, rew, done, act in data.seq_iter(num_epochs=1, max_sequence_len=32):
    print("Number of diffrent actions:", len(act))
    for action in act:
        print(act)
    print("Number of diffrent observations:", len(obs), obs)
    for observation in obs:
        print(obs)
    print("Rewards:", rew)
    print("Dones:", done)
```

## MineRL Competition
If you're here for the MineRL competition. Please check [the main competition website here](https://www.aicrowd.com/challenges/neurips-2019-minerl-competition).
