# MineRL Environments
The MineRL competition will be run in `MineRLObtainDiamond-v0` - this environment and other auxiliary environments available for both testing and training are outlined below. 

> Note: The MineRL obtain item environments, including `MineRLObtainDaimond-v0` are are not yet published

Action spaces are defined by ordered n-tuples  
Info spaces are defined by dictionary spaces {str: numpy.float32}  
Observation and Reward spaces are single numpy arrays corresponding to the POV of the agent and the reward at each time step respectively


## MineRLTreechop-v0
> This could be a good place to add a description of the task for participants who are un-familiar with the environment
##### Observation Space
* `minerl.pov_observation(hight=64, width=64, chanels=3, dtype=uint8)`
##### Info Space
* `minerl.flat_inventory_obs(['minecraft:log', 'minecraft:log2'])`
##### Action Space
* `minerl.continuous_movement_commands()`
* `minerl.attack_command()`
##### Reward Space
* `minerl.reward_for_collecting_item({'minecraft:log': 1, 'minecraft:log2': 1})`

## MineRLNavigate-v0
##### Observation Space
* `minerl.pov_observation(hight=64, width=64, chanels=3, dtype=uint8)`
##### Info Space
* `minerl.compass_angle_observation(min=0, max=1, dtype=float32)`
##### Action Space
* `minerl.continuous_movement_commands()`
* `minerl.attack_command()`
##### Reward Space
* `minerl.reward_for_touching_block({'minecraft:diamond_block': 100})`

## MineRLNavigateDense-v0
##### Observation Space
* `minerl.pov_observation(hight=64, width=64, chanels=3, dtype=uint8)`
##### Info Space
* `minerl.compass_angle_observation(min=0, max=1, dtype=float32)`
##### Action Space
* `minerl.continuous_movement_commands()`
* `minerl.attack_command()`
##### Reward Space
* `minerl.reward_for_touching_block({'minecraft:diamond_block': 100})`
* `minerl.reward_for_walking_towards_compass_target(reward_per_block=1)`
