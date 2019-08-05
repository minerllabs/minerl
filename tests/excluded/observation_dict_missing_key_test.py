# Test that an appropriate error is raised when an expected key is 
# missing from an observation dict.
from minerl.env import spaces
from minerl.env.core import MineRLEnv, missions_dir
from minerl.env.comms import FatalException

import os


def main():
    """
    Tests that an appropriate error is raised when an expected key 
    is missing from an observation dict.
    """
    xml = os.path.join(missions_dir, 'navigation.xml')

    observation_space = spaces.Dict({
        'missing_key': spaces.Discrete(2), # A key that will be absent
    })

    action_space = spaces.Dict(spaces={
        "forward": spaces.Discrete(2), 
    })

    env = MineRLEnv(xml, observation_space, action_space)
    
    try:
        env.reset()
        print("Failure: Malformed env reset without an exception.")
    except FatalException as e:
        print("Success: FatalException was properly thrown:")
        raise e

if __name__ == "__main__":
    main()
