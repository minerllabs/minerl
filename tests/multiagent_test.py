from minerl.herobraine.env_specs.treechop_specs import Treechop
import gym
import minerl  # noqa
import argparse
import time

class TreechopMultiAgentNoQuit(Treechop):
    def create_server_quit_producers(self):
        return [

        ]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--single', action="store_true", help='use the single agent default xml')
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

    # make env
    if args.single:
        env_spec = Treechop(agent_count=1)
    else:
        env_spec = Treechop(agent_count=2)

    env = env_spec.make( port=args.port)


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
            
            actions = env.action_space.no_op()
            for agent in actions:
                actions[agent]["forward"] = 1
                actions[agent]["attack"] = 1
                actions[agent]["camera"] = [0,0.1]

            # print(str(steps) + " actions: " + str(actions))
        
            obs, reward, done, info = env.step(actions)

            # log("reward: " + str(reward))
            # log("done: " + str(done))
            # log("info: " + str(info))
            # log(" obs: " + str(obs))

        logging.debug(f"Episode {r + 1}/{args.episodes} done: {steps} steps")

