
from minerl import env
from minerl import data


def main():
    data = data.init()
    env = env.init()
    obs = env.reset()

    while not data.finished():
        human_obs, human_reward = data.sample()

    actionSpace = env.getActionSpace()

    while not env.isFinished():
        action = actionSpace.sample()
        human_obs = data.get()
        env_obs, reward = env.step(action)

