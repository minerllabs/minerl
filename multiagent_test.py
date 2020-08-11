import gym
import minerl  # noqa
import argparse
from pathlib import Path
import time
from lxml import etree


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=str, default='MineRLNavigateDense-v0', help='the gym env')
    # parser.add_argument('--env', type=str, default='MineRLNavigateDense-v0', help='the gym env')
    parser.add_argument('--xml', type=str, default='minerl/env/Malmo/MalmoEnv/missions/mobchase_two_agents.xml', help='the mission xml path')
    parser.add_argument('--port', type=int, default=9000, help='the mission server port')
    parser.add_argument('--episodes', type=int, default=1, help='the number of resets to perform - default is 1')
    args = parser.parse_args()

    # logs
    import coloredlogs
    import logging
    coloredlogs.install(level=logging.DEBUG)

    # clear logs
    import subprocess
    print("deleting existing java log files...")
    subprocess.check_call("rm -rf logs/*", shell=True)

    xml = Path(args.xml).read_text()

    mission = etree.fromstring(xml)  # TODO - this should be the full parsing from MineRLEnv
    number_of_agents = len(mission.findall('{http://ProjectMalmo.microsoft.com}AgentSection'))
    print("Number of agents: " + str(number_of_agents))

    env = gym.make(args.env, xml=args.xml, port=None)#args.port)

    for r in range(args.episodes):
        print("reset " + str(r))
        env.reset()
        steps = 0

        done = False
        while not done:
            steps += 1
            env.render()

            actions = [env.action_space.sample() for _ in range(number_of_agents)]
            # print(str(steps) + " actions: " + str(actions))

            obs, reward, done, info = env.step(actions)
            # log("reward: " + str(reward))
            # log("done: " + str(done))
            # log("info: " + str(info))
            # log(" obs: " + str(obs))

            time.sleep(.05)

    env.close()
