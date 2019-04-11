
from MineRL import MalmoEnv
from MineRL import Data


def main():
    data = Data.init()
    env = MalmoEnv.init()
    obs = env.reset()

    while not data.finished():
        human_obs, human_reward = data.step()

    actionSpace = env.getActionSpace()

    while not env.isFinished():
        action = actionSpace.sample()
        human_obs = data.get()
        env_obs, reward = env.step(action)

