import minerl
import gym
import threading
import argparse
import time
import logging
import coloredlogs
coloredlogs.install(logging.DEBUG)



def main():
    """
    Runs a test which runs many instances of minerl simultaneously.
    """
    parser = argparse.ArgumentParser(description='The multi-environment stress test.')
    parser.add_argument("ninstances", help='Number of instances', type=int)

    opts = parser.parse_args()
    should_stop = False
    should_start = False

    def run_instance():
        nonlocal should_stop, should_start
        try:
            env.reset() 
            done = False
            while not (done or should_stop):
                env.step(env.action_space.sample())
        except:
            pass

    threads = []

    for _ in range(opts.ninstances):
        env = gym.make('MineRLTreechop-v0')
        # time.sleep(3) # Wait for  the thread to start.
        threads.append(threading.Thread(target=run_instance, args=(env)))

    for thread in threads:
        thread.start()
    
    should_start = True
    time.sleep(100) # Wait for the thread to finish.
    should_stop = True


if __name__ == '__main__':
    main()