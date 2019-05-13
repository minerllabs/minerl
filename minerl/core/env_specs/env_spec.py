

class EnvSpec:
    def __init__(self, resolution):
        self.resolution = tuple(resolution)
        return

    def create_mission_handlers(self):
        raise NotImplementedError('subclasses must override create_mission_handlers()!')

    def create_observables(self):
        raise NotImplementedError('subclasses must override create_observables()!')

    def create_actionables(self):
        raise NotImplementedError('subclasses must override create_actionables()!')
