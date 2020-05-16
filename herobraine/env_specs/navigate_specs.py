from typing import List

import herobraine
import herobraine.hero.handlers as handlers
from herobraine.env_specs.env_spec import EnvSpec


class Navigate(EnvSpec):
    def __init__(self, name='MineRLNavigate-v0'):
        self.resolution = tuple((64, 64))
        self.episode_len = 300
        super().__init__(name, self.resolution)

    @staticmethod
    def is_from_folder(folder: str) -> bool:
        return folder == 'navigate'

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        mission_handlers = [
            handlers.EpisodeLength(self.episode_len),
            handlers.RewardForTouchingBlock(
                {"diamond_block", 100.0}
            ),
            handlers.NavigateTargetReward(),
            handlers.NavigationDecorator(
                min_radius=64,
                max_radius=64,
                randomize_compass_target=True
            )
        ]
        return mission_handlers

    def create_observables(self) -> List[herobraine.hero.AgentHandler]:
        observables = [
            handlers.POVObservation(self.resolution),
            handlers.CompassObservation()]
        return observables

    def create_actionables(self) -> List[herobraine.hero.AgentHandler]:
        actionables = [
            handlers.KeyboardAction("move", "S", "W"),
            handlers.KeyboardAction("strafe", "A", "D"),
            handlers.KeyboardAction("jump", "SPACE"),
            handlers.KeyboardAction("crouch", "SHIFT"),
            handlers.KeyboardAction("attack", "BUTTON0"),
            # TODO place opaque block command
            # handlers.KeyboardAction("use", "BUTTON1"),
        ]
        actionables += [handlers.MouseAction("pitch", "cameraPitch")]
        actionables += [handlers.MouseAction("turn", "cameraYaw")]
        return actionables


class NavigateExtreme(Navigate):
    def __init__(self, name='MineRLNavigateExtreme-v0'):
        super().__init__(name)


class NavigateDense(Navigate):
    def __init__(self, name='MineRLNavigateDense-v0'):
        super().__init__(name)
        pass

    def create_mission_handlers(self) -> List[herobraine.hero.AgentHandler]:
        mission_handlers = super().create_mission_handlers()
        mission_handlers.append(handlers.RewardForWalkingTwardsTarget(
            reward_per_block=1, reward_schedule="PER_TICK"
        ))
        return mission_handlers


class NavigateExtremeDense(NavigateDense):
    def __init__(self, name='MineRLNavigateExtremeDense-v0'):
        super().__init__(name)


class NavigateInventory(NavigateDense):
    def __init__(self, name='MineRLNavigateDenseInventory-v0'):
        super().__init__(name)
        pass

    def create_observables(self) -> List[herobraine.hero.AgentHandler]:
        observables = super().create_observables()
        observables += handlers.FlatInventoryObservation(["dirt"])

        return observables

    def create_actionables(self) -> List[herobraine.hero.AgentHandler]:
        actionables = super().create_actionables()
        actionables += handlers.PlaceBlock(['dirt'])
        return actionables
