# MineRL Environments
The MineRL competition will be run in `MineRLObtainDiamond-v0` - this environment and other auxiliary environments available for both testing and training are outlined below. 

> Note: The MineRL obtain item environments, including `MineRLObtainDaimond-v0` are are not yet published


## MineRLTreechop-v0
> This could be a good place to add a description of the task for participants who are un-familiar with the environment
##### Observation Space:
* `minerl.pov_observation(hight=64, width=64, chanels=3, dtype=uint8)`
##### Info Space:
* `minerl.flat_inventory_obs(['minecraft:log', 'minecraft:log2'])`
##### Action Space
* `minerl.continuous_movement_commands()`
* `minerl.attack_command()`
##### Reward Space
* `minerl.reward_for_collecting_item({'minecraft:log': 1, 'minecraft:log2': 1})`

## MineRLNavigate-v0
#### Info Space:
* `minerl.flat_inventory_obs(['minecraft:log', 'minecraft:log2'])`
* `minerl.agent_health_obs()`
* `minerl.agent_hunger_obs()`
##### Action Space
* `minerl.continuous_movement_commands()`
* `minerl.attack_command()`
##### Reward Space
* `minerl.reward_for_collecting_item({'minecraft:log': 1, 'minecraft:log2': 1})`

## MineRLNavigateDense-v0
#### Info Space:
* `minerl.flat_inventory_obs(['minecraft:log', 'minecraft:log2'])`
* `minerl.agent_health_obs()`
* `minerl.agent_hunger_obs()`
##### Action Space
* `minerl.continuous_movement_commands()`
* `minerl.attack_command()`
##### Reward Space
* `minerl.reward_for_collecting_item({'minecraft:log': 1, 'minecraft:log2': 1})`