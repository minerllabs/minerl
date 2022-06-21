"""To launch this test do the following.

1. Launch Pyro4-ns

    pyro4-ns

2. Launch the instance manager

python3 -c "from ai_crowd_specified_seed_test import lim; lim()" --seeding_type=3 --seeds 1,1,1;2,2,2

3. Run the test.

python3 -m ai_crowd_specified_seed_test
"""

import os
import subprocess
import io

import time
import threading
import Pyro4


def launch_ns():
    """Launches the pyro4-ns if it doesn't already exist.

    Returns the process.
    """
    return subprocess.Popen(["pyro4-ns"], shell=False)


def launch_im():
    return subprocess.Popen(
        'python3 scripts/launch_instance_manager.py --seeding_type=3 --seeds=1,1,1,1;2,2,2,2'.split(' '), shell=False)


def main():
    """Tests multi-instance seeding.
    """
    # try:
    #     # 1. Launch the pyro4-ns if it doesn't exist
    #     ns =launch_ns()
    #     print("launched!")
    #     time.sleep(1)
    #     im = launch_im()
    #     time.sleep(2)

    # envs = []

    import gym
    os.environ['MINERL_INSTANCE_MANAGER_REMOTE'] = '1'
    import minerl

    def run_env():
        try:
            env = gym.make('MineRLNavigateDense-v0')
        except Exception as e:
            print("Pyro traceback:")
            print("".join(Pyro4.util.getPyroTraceback()))
            raise e

        for _ in range(3):
            env.reset()
            for _ in range(100):
                env.step(env.action_space.no_op())
                # env.render()

    thrs = [threading.Thread(target=run_env) for _ in range(2)]
    for t in thrs:
        time.sleep(1)
        t.start()

    for t in thrs:
        t.join()

    # finally:


if __name__ == '__main__':
    main()
