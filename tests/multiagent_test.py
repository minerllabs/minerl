import gym
import minerl  # noqa
import argparse
from pathlib import Path
import time
from lxml import etree
import numpy as np


DEFAULT_SINGLE_AGENT_XML = 'tests/single_agent.xml'
DEFAULT_MULTI_AGENT_XML = 'tests/two_agents.xml'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=str, default='MineRLNavigateDense-v0', help='the gym env')
    parser.add_argument('--single', action="store_true", help='use the single agent default xml')
    parser.add_argument('--xml', type=str, default=None, help='the mission xml path, None uses single/multi default')
    parser.add_argument('--port', type=int, default=None, help='the port of existing client or None to launch')
    parser.add_argument('--episodes', type=int, default=1, help='the number of resets to perform - default is 1')
    args = parser.parse_args()

    # logs
    import coloredlogs
    import logging
    coloredlogs.install(level=logging.DEBUG)

    # clear logs
    import subprocess
    logging.debug("Deleting previous java log files...")
    subprocess.check_call("rm -rf logs/*", shell=True)

    # check if default xmls should be used
    xml_path = args.xml
    if xml_path is None:
        if args.single:
            xml_path = DEFAULT_SINGLE_AGENT_XML
        else:
            xml_path = DEFAULT_MULTI_AGENT_XML

    # make env
    xml = Path(xml_path).read_text()
    env = gym.make(args.env, xml=xml, port=args.port)

    # iterate desired episodes
    for r in range(args.episodes):
        logging.debug(f"Reset for episode {r + 1}")
        env.reset()
        steps = 0

        done = False
        actor_names = env.actor_names
        while not done:
            steps += 1
            env.render()

            actions = {actor_name: env.action_space.sample() for actor_name in actor_names}
            # print(str(steps) + " actions: " + str(actions))

            obs, reward, done, info = env.step(actions)

            # log("reward: " + str(reward))
            # log("done: " + str(done))
            # log("info: " + str(info))
            # log(" obs: " + str(obs))

            time.sleep(.05)
        logging.debug(f"Episode {r + 1}/{args.episodes} done: {steps} steps")

    env.close()
