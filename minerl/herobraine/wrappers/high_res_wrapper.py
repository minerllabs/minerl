from collections import OrderedDict

from minerl.herobraine.wrapper import EnvWrapper
from minerl.herobraine.hero import handlers


class HighRes(EnvWrapper):
    """
        Replaces all POV observation with a different (presumably higher) resolution.
    """
    def __init__(self, env_to_wrap, resolution=(1024, 1024)):
        self.resolution = resolution
        super().__init__(env_to_wrap)

    def _update_name(self, name: str) -> str:
        task, ver = name.split('-')
        return task + "HighRes-" + ver

    def create_observables(self):
        observables = super().create_observables()
        new_pov = handlers.POVObservation(self.resolution)
        result = []
        found = False
        for handler in observables:
            if isinstance(handler, handlers.POVObservation):
                assert not found
                found = True
                result.append(new_pov)
            else:
                result.append(handler)
        assert found
        return result

    def _wrap_action(self, act: OrderedDict) -> OrderedDict:
        return act

    def _wrap_observation(self, obs: OrderedDict) -> OrderedDict:
        return obs

    def _unwrap_action(self, act: OrderedDict) -> OrderedDict:
        return act

    def _unwrap_observation(self, obs: OrderedDict) -> OrderedDict:
        return obs
