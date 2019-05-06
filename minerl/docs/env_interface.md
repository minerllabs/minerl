# MineRL Environments



## MineRLTreechop-v0
#### Info Space:
* `minerl.flat_inventory_obs(['minecraft:log', 'minecraft:log2'])`
##### Action Space
* `minerl.continuous_movement_commands()`
* `minerl.attack_command()`
##### Reward Space
* `minerl.reward_for_collecting_item({'minecraft:log': 1, 'minecraft:log2': 1})`

## MineRLTreechop-v0
#### Info Space:
* `minerl.flat_inventory_obs(['minecraft:log', 'minecraft:log2'])`
* `minerl.agent_health_obs()`
* `minerl.agent_hunger_obs()`
##### Action Space
* `minerl.continuous_movement_commands()`
* `minerl.attack_command()`
##### Reward Space
* `minerl.reward_for_collecting_item({'minecraft:log': 1, 'minecraft:log2': 1})`