from xml.etree.ElementTree import Element

from minerl.herobraine.hero import AgentHandler


class TickHandler(AgentHandler):
    """
    Overrides tick speeds.
    """

    def __init__(self, ms_per_tick):
        self.ms_per_tick = ms_per_tick
        super().__init__(None)

    def add_to_mission_xml(self, etree: Element, namespace : str):

        for mspertick in etree.iter('{{{}}}MsPerTick'.format(namespace)):
            mspertick.text = str(self.ms_per_tick)

class EpisodeLength(AgentHandler):
    """
    Overrides tick speeds.
    """

    def __init__(self, episode_length):
        self.episode_length = episode_length
        super().__init__(None)

    def add_to_mission_xml(self, etree: Element, namespace: str):
        for mspertick in etree.iter('{{{}}}ServerQuitFromTimeUp'.format(namespace)):
            mspertick.set('timeLimitMs', '{}'.format(str(self.episode_length)))

class NavigationDecorator(AgentHandler):
    """
    Overrides placement of navigation target for navigation decorator
    """

    def __init__(self, max_radius=64, min_radius=None, randomize_compass_target=True, min_offset=0, max_offset=8):
        # Error in compass target
        self.randomize_target = randomize_compass_target
        self.min_target_offset = min_offset
        self.max_target_offset = max_offset

        # Placement for diamond block
        self.block = 'diamond_block'
        self.placement = 'surface'
        self.max_radius = max_radius
        self.min_radius = min_radius if min_radius is not None else max_radius
        super().__init__(None)

    def add_to_mission_xml(self, etree: Element, namespace: str):
        # TODO implement to XML and remove decorator from navigate XMLs
        pass
        # NavigationDecorator.add_min_radius_to_xml(etree, namespace, self.min_radius)
        # NavigationDecorator.add_max_radius_to_xml(etree, namespace, self.max_radius)
        # NavigationDecorator.add_block_type_to_xml(etree, namespace, self.block)
        # NavigationDecorator.add_placement_to_xml(etree, namespace, self.placement)
        #
        # NavigationDecorator.add_random_compass_target_to_xml(etree, namespace, self.randomize_target)
        # NavigationDecorator.add_min_target_offset_to_xml(etree, namespace, self.min_target_offset)
        # NavigationDecorator.add_max_target_offset_to_xml(etree, namespace, self.max_target_offset)

    @staticmethod
    def add_placement_to_xml(etree, namespace, placement):
        for entry in etree.iter('{{{}}}randomPlacementProperties'.format(namespace)):
            entry.set('placement', '{}'.format(str(placement)))
    @staticmethod
    def add_block_type_to_xml(etree, namespace, block_type):
        for entry in etree.iter('{{{}}}randomPlacementProperties'.format(namespace)):
            entry.set('placement', '{}'.format(str(block_type)))

    @staticmethod
    def add_min_radius_to_xml(etree, namespace, min_radius):
        for entry in etree.iter('{{{}}}randomPlacementProperties'.format(namespace)):
            entry.set('minRandomizedRadius', '{}'.format(str(min_radius)))
    @staticmethod
    def add_max_radius_to_xml(etree, namespace, max_radius):
        for entry in etree.iter('{{{}}}randomPlacementProperties'.format(namespace)):
            entry.set('maxRandomizedRadius', '{}'.format(str(max_radius)))


    @staticmethod
    def add_random_compass_target_to_xml(etree, namespace, randomise_target):
        for entry in etree.iter('{{{}}}NavigationDecorator'.format(namespace)):
            entry.set('randomizeCompassLocation', '{}'.format(str(randomise_target)))
    @staticmethod
    def add_min_target_offset_to_xml(etree, namespace, min_distance):
        for entry in etree.iter('{{{}}}NavigationDecorator'.format(namespace)):
            entry.set('minRandomizedDistance', '{}'.format(str(min_distance)))
    @staticmethod
    def add_max_target_offset_to_xml(etree, namespace, max_distance):
        for entry in etree.iter('{{{}}}NavigationDecorator'.format(namespace)):
            entry.set('maxRandomizedDistance', '{}'.format(str(max_distance)))

