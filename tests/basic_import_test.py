# Basic package test
import os

import gym
import minerl

def main(): 
    """
    Tests importing of gym envs
    """
    print(os.environ['JAVA_HOME'])
    spec = gym.spec('MineRLNavigate-v0')
    spec = gym.spec('MineRLNavigateDense-v0')
    spec = gym.spec('MineRLNavigateExtreme-v0')
    spec = gym.spec('MineRLNavigateExtremeDense-v0')
    spec = gym.spec('MineRLObtainIronPickaxe-v0') 
    spec = gym.spec('MineRLObtainIronPickaxeDense-v0')
    spec = gym.spec('MineRLObtainDiamond-v0')
    spec = gym.spec('MineRLObtainDiamondDense-v0')

    print("Test complete.")
    return True


def test_import():
    print(minerl.data.version)
    assert main() is True


if __name__ == '__main__':
    main()

