import logging

import gym


def _agent_seems_alive(obs: dict) -> bool:
    """Return True if there are any items in inventory (a telltale sign of agent death is
    dropping all items)"""
    inventory = obs["inventory"]
    for count in inventory.values():
        if count > 0:
            return True
    return False


class RetryResetOnEarlyDeathWrapper(gym.Wrapper):
    """
    Apply this wrapper directly over a MineRLEnv with a VillageSpawnDecorator to
    reset() when the agent dies ~instantly due to spawning inside a wall.

    Can also make it seem as if the agent spawned on the ground instead of in the air
    because as a side effect this wrapper will call `self.env.step(noop_act)` several
    times to check if the player has died immediately after `reset()`.

    WARNING: This wrapper may have unexpected interactions with `seed()`, which otherwise
    guarantees that the agent spawns in the ~same village every time.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, env, n_reset_attempts=3, n_noops=30):
        assert n_reset_attempts > 0
        assert n_noops >= 0
        self.n_reset_attempts = n_reset_attempts
        self.n_noops = n_noops
        super().__init__(env)

    def reset(self):
        for attempt_count in range(self.n_reset_attempts):
            obs = self.env.reset()
            # noop() is not guaranteed to exist unless `self.env` is a MineRLEnv.
            # Therefore, this wrapper should be directly applied on top of the MineRLEnv.
            noop_act = self.env.action_space.noop()

            done = False
            for _ in range(self.n_noops):
                obs, _, done, _ = self.env.step(noop_act)
                if done:
                    # Environment ended early for some reason. Assume early death and
                    # continue on to the next reset attempt.
                    break

            if not done and _agent_seems_alive(obs):
                # Agent has survived for n_noop steps. We are now ready to start the
                # episode in earnest.
                return obs
            else:
                self.logger.info(
                    f"Agent died within {self.n_noops} ticks after reset "
                    f"(attempt {attempt_count + 1} out of {self.n_reset_attempts}). "
                    "For more information on death circumstances, set environment variable "
                    "MINERL_DEBUG_LOG=1 to see more Malmo/Minecraft logs."
                )

        raise RuntimeError(
            f"Agent died within {self.n_noops} steps every time in each of "
            f"{self.n_reset_attempts} attempts"
        )
