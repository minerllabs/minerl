
import gym.spaces as spaces
# TODO: Make this minerl spaces

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

    def get_observation_space(self):
        # Todo: handle nested dict space.
        
        ss = {
            o.to_string(): o.space for o in self.create_observables() if not hasattr(o, 'hand')
        }
        try:
            ss.update({
                'equipped_items': spaces.Dict({
                    'mainhand': spaces.Dict({
                         o.to_string(): o.space for o in self.create_observables() if hasattr(o, 'hand')
                    })
                })
            })
        except Exception as e:
            print(e)
            pass
            
        return spaces.Dict(spaces=ss)

    def get_action_space(self):
        return spaces.Dict(spaces={
            a.to_string(): a.space for a in self.create_actionables()
        })