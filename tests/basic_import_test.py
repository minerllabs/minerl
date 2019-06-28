# Basic package test
import gym
import minerl


def main():
    """
    Tests importing of gym envs
    """
    env = gym.make('MineRLNavigate-v0')
    env = gym.make('MineRLNavigateDense-v0')
    env = gym.make('MineRLNavigateExtreme-v0')
    env = gym.make('MineRLNavigateExtremeDense-v0')
    env = gym.make('MineRLObtainIron-v0')
    env = gym.make('MineRLObtainIronDense-v0')
    env = gym.make('MineRLObtainDiamond-v0')
    env = gym.make('MineRLObtainDiamondDense-v0')

    print("Test complete.")


main()
