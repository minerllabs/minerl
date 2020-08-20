




from typing import Any, Dict, Tuple
from minerl.env.multiagent import MultiAgentEnv
from collections import Iterable


class SingleAgentEnv(MultiAgentEnv):
    """The single agent version of the MineRLEnv.
    
    """
    def __init__(self, *args, **kwargs):
        super(SingleAgentEnv, self).__init__(*args, **kwargs)
        assert self.env_spec.agent_count == 1, (
            "Using the minerl.env.SingleAgentEnv when multiple agents are specified. Error.")

    def reset(self) -> Dict[str, Any]:
        multi_obs = super().reset()
        return multi_obs[self.env_spec.agent_names[0]]

    def step(self, single_agent_action : Dict[str, Any]) -> Tuple[
        Dict[str, Any], float, bool, Dict[str, Any]]:
        aname = self.env_spec.agent_names[0]
        multi_agent_action = {
            aname: single_agent_action
        }
        obs, rew, done, info =  super().step(multi_agent_action)

        return obs[aname], rew[aname], done, info

    def _check_action(self, actor_name, action, env_spec):
        # With a single agent the envspec doesn't contain actor naems in the action space.
        return action in env_spec.action_space 