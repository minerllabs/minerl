import numpy as np

from minerl.env import spaces
from minerl.env.constants import ALL_ITEMS, Buttons, ITEMS_SPACE

unified_observation_space = spaces.Dict({
    'pov': spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
    'inventory': spaces.Dict({item: spaces.Box(low=0, high=2304, shape=(), dtype=np.int) for item in ALL_ITEMS}),
    'equipped_items': spaces.Dict({
        'mainhand': spaces.Dict({
            'type': ITEMS_SPACE,
            'damage': spaces.Box(low=-1, high=1562, shape=(), dtype=np.int),
            'maxDamage': spaces.Box(low=-1, high=1562, shape=(), dtype=np.int),
        })
    }),
    'life': spaces.Box(low=0,high=20, shape=(), dtype=np.float),
    'score': spaces.Box(low=0, high=1395, shape=(), dtype=np.int),
    'food': spaces.Box(low=0, high=20,shape=(), dtype=np.int),
    'saturation': spaces.Box(low=0, high=5, shape=(), dtype=np.float),
    'xp': spaces.Box(low=0, high=1395, shape=(), dtype=np.int),
    'breath': spaces.Box(low=0, high=300, shape=(), dtype=np.int),
})

binary_actions = {b: spaces.Discrete(2) for b in Buttons.ALL}
all_actions = {
    "camera": spaces.Box(low=-180, high=180, shape=(2,), dtype=np.float32),  # Pitch, Yaw
    "place": ITEMS_SPACE,
    "equip": ITEMS_SPACE,
    "craft": ITEMS_SPACE,
    "nearbyCraft": ITEMS_SPACE,
    "nearbySmelt": ITEMS_SPACE,
     }
all_actions.update(binary_actions)

unified_action_space = spaces.Dict(all_actions)