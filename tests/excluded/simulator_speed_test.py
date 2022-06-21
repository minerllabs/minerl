import minerl
import IPython
import gym
import coloredlogs
import logging
import time
import numpy as np

coloredlogs.install(level=logging.DEBUG)


def run_episode(thr_num, *args):
    env = gym.make('MineRLTreechop-v0')
    env.make_interactive(port=5656, realtime=True)
    env.seed(17)
    for _ in range(1000):
        env.reset()
        done = False
        timings = []
        while not done:
            t0 = time.time()
            act = env.action_space.noop()
            act['forward'] = 1
            act['jump'] = 1
            act['attack'] = 1
            _, _, done, _ = env.step(act)
            env.render()
            timings.append(time.time() - t0)
            if len(timings) % 1000 == 0 or done:
                print(thr_num, ": ", 1 / np.mean(timings))
            # time.sleep(.1)


if __name__ == '__main__':
    run_episode(0)
