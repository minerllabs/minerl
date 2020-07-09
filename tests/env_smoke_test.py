import gym
import pytest

@pytest.mark.skip(reason='suspected as slow, > 5min. TODO (peterz) fix')
def test_treechop_smoke():
    with gym.make('minerl:MineRLTreechop-v0') as env:
        env.reset()
        for _ in range(10):
            env.step(env.action_space.sample())
