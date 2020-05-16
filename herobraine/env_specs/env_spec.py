

class EnvSpec:
    def __init__(self, name, resolution):
        self.name = name
        self.resolution = tuple(resolution)
        return

    def to_string(self):
        return self.name

    @staticmethod
    def is_from_folder(folder: str) -> bool:
        raise NotImplementedError('subclasses must override is_from_folder()!')

    def create_mission_handlers(self):
        raise NotImplementedError('subclasses must override create_mission_handlers()!')

    def create_observables(self):
        raise NotImplementedError('subclasses must override create_observables()!')

    def create_actionables(self):
        raise NotImplementedError('subclasses must override create_actionables()!')
