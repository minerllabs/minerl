
import minerl
import IPython
import gym
import coloredlogs
import logging
import time
import numpy as np
coloredlogs.install(level=logging.INFO)



def run_episode(thr_num, *args):
 env = gym.make('MineRLTreechop-v0')
 env.seed(17)
 for _ in range(1000):
   env.reset()
   done = False
   timings = []
   while not done:
      t0 = time.time()
      _,_,done,_ =   env.step(env.action_space.noop())
      timings.append(time.time() - t0)
      if len(timings)  % 1000 == 0 or done:
         print(thr_num, ": ", 1/np.mean(timings))


import threading


threads = [threading.Thread(target=run_episode, args=(_,)) for _ in range(1)]

for thr in threads:
   thr.start()
   time.sleep(5)

