
class CompassObservation(TranslationHandler, SimpleXMLElementMixin):
    """
    Handles compass observations.
    """
    logger = logging.getLogger(__name__ + ".CompassObservation")

    def to_string(self):
        return 'compassAngle'

    def __init__(self):

        super().__init__(spaces.Box(low=-180.0, high=180.0, shape=(), dtype=np.float32))

    def from_universal(self, obs):
        y = np.array(((obs["compass"]["angle"] * 360.0 + 180) % 360.0) - 180)
        return y

    def from_hero(self, obs):
        return np.array((obs['angle'] + 0.5) % 1.0)

    @property
    def xml_element(self) -> str:
        return "ObservationFromCompass"


class CompassDistanceObservation(SimpleObservationHander):
    """
    Handles compass observations.
    NOT FOR USE IN THE NAVIGATE MISSIONS.
    """
    logger = logging.getLogger(__name__ + ".CompassDistanceObservation")

    def to_string(self):
        return 'compass_distance'

    def __init__(self):

        super().__init__(
            hero_keys=["distance"],
            univ_keys=['compass']["distance"],
            space=spaces.Box(low=0, high=128, shape=(1,), dtype=np.uint8))

    def from_universal(self, obs):
        return np.array([obs['compass']['distance']])

    def from_hero(self, obs):
        return np.array([obs['distance']])

       


# TODO: UPDATE CHAT OBSERVATION
class ChatObservation(AgentHandler):
    """
    Handles chat observations.
    """

    def to_string(self):
        return 'chat'

    def __init__(self):
        super().__init__(spaces.Text([1]))

    def add_to_mission_spec(self, mission_spec):
        mission_spec.observeChat()

    def from_hero(self, x):
        # Todo: From Hero
        raise NotImplementedError()

