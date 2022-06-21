# # Copyright (c) 2020 All Rights Reserved
# # Author: William H. Guss, Brandon Houghton


from typing import Any, Dict, Tuple
from minerl.env._multiagent import _MultiAgentEnv


class _SingleAgentEnv(_MultiAgentEnv):
    """The single agent version of the MineRLEnv.

    THIS CLASS SHOULD NOT BE INSTANTIATED DIRECTLY
    USE ENV SPEC.
    """

    def __init__(self, *args, **kwargs):
        super(_SingleAgentEnv, self).__init__(*args, **kwargs)
        assert self.task.agent_count == 1, (
            "Using the minerl.env._SingleAgentEnv when multiple agents are specified. Error.")

    def reset(self) -> Dict[str, Any]:
        multi_obs = super().reset()
        return multi_obs[self.task.agent_names[0]]

    def step(self, single_agent_action: Dict[str, Any]) -> Tuple[
        Dict[str, Any], float, bool, Dict[str, Any]]:
        aname = self.task.agent_names[0]
        multi_agent_action = {
            aname: single_agent_action
        }
        obs, rew, done, info = super().step(multi_agent_action)

        return obs[aname], rew[aname], done, info[aname]

    def render(self, mode='human'):
        return super().render(mode)[self.task.agent_names[0]]

    def _check_action(self, actor_name, action, env_spec):
        # TODO: Refactor to move to the env spec.
        # With a single agent the envspec doesn't contain actor names in the action space.
        # if not all([action[key] in env_spec.action_space[key] for key in action]):
        #     for key in action:
        #         if action[key] not in env_spec.action_space[key]:
        #             print(key)
        #             print(action[key])
        #             print(env_spec.action_space[key])
        return all([action[key] in env_spec.action_space[key] for key in action])
        # TODO validate above works as intended - below was failing for unknown reasons
        # return action in env_spec.action_space
