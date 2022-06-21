import logging
import pytest
from flaky import flaky
from minerl.herobraine.env_specs.human_survival_specs import HumanSurvival

import coloredlogs
coloredlogs.install(logging.DEBUG)

@pytest.mark.parametrize("resolution", [(1280, 720), (640, 360), (640, 480)])
@flaky
def test_turn(resolution):
    env = HumanSurvival(resolution=resolution).make()
    env.reset()
    _, _, _, info = env.step(env.action_space.noop())
    yawstart = info['location_stats']['yaw']   
    pitchstart = info['location_stats']['pitch']   
    dpitch = 5
    N = 30
    for i in range(N):
        ac = env.action_space.noop()
        ac['camera'] = [0.0, 360 / N]
        _, _, _, info = env.step(ac)
    assert abs(info['location_stats']['yaw'] % 360 - yawstart % 360) < 1
    ac = env.action_space.noop()
    ac['camera'] = [dpitch, 0]
    _, _, _, info = env.step(ac)
    assert abs(info['location_stats']['pitch'] - pitchstart - dpitch) < 1

if __name__ == '__main__':
    test_turn((640, 360))



