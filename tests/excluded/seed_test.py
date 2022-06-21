import json
import select
import time
import logging

import gym
import minerl
import numpy as np

import coloredlogs

coloredlogs.install(logging.DEBUG)

# import minerl.env.bootstrap
# minerl.env.bootstrap._check_port_avail = lambda _,__: True

NUM_EPISODES = 10


def main():
    """
    Tests running a simple environment.
    """
    env = gym.make('MineRLNavigateDense-v0')

    actions = [env.action_space.sample() for _ in range(2000)]
    xposes = []
    reward_list = []
    for _ in range(NUM_EPISODES):
        env.seed(22)
        obs = env.reset()
        done = False
        netr = 0
        rewards = []
        while not done and len(rewards) < 50:
            random_act = env.action_space.noop()
            # if(len(rewards) > 50):

            random_act['camera'] = [0, 0.1]
            random_act['back'] = 0
            random_act['forward'] = 1
            random_act['jump'] = 1
            random_act['attack'] = 1
            # print(random_act)
            obs, reward, done, info = env.step(
                random_act)
            env.render()
            rewards.append(reward)
            netr += reward
            # print(reward, netr)
        reward_list.append(rewards)
    import matplotlib.pyplot as plt
    for t in range(NUM_EPISODES):
        plt.plot(np.cumsum(reward_list[t]))
    # plt.plot(np.cumsum(reward_list[1]))
    plt.show()
    # from IPython import embed; embed()
    input()

    print("Demo complete.")


if __name__ == "__main__":
    main()
