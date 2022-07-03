import logging
import gym
from minerl.herobraine.env_specs.human_survival_specs import HumanSurvival

import coloredlogs
coloredlogs.install(logging.DEBUG)

def test_turn(resolution):
    #env = HumanSurvival(resolution=resolution).make()
    #env = gym.make("MineRLBasaltBuildVillageHouse-v0")
    env = gym.make("MineRLObtainDiamondShovel-v0")
    #env = gym.make("MineRLBasaltFindCave-v0")
    env.reset()
    _, _, _, info = env.step(env.action_space.noop())
    N = 100
    for i in range(N):
        ac = env.action_space.noop()
        ac['camera'] = [0.0, 360 / N]
        _, _, _, info = env.step(ac)
        env.render()
    env.close()

if __name__ == '__main__':
    test_turn((640, 360))



