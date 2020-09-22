# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton


#  <BiomeGenerator forceReset="true" biome="3"/>
from minerl.herobraine.hero.handler import Handler
import jinja2


# <Time>
#     <StartTime>6000</StartTime>
#     <AllowPassageOfTime>false</AllowPassageOfTime>
# </Time>
class TimeInitialCondition(Handler):
    def to_string(self) -> str:
        return "time_initial_condition"

    def xml_template(self) -> str:
        return str(
            """<Time>
                   {% if start_time is not none %}
                   <StartTime>{{start_time | string}}</StartTime>
                   {% endif %}
                   <AllowPassageOfTime>{{allow_passage_of_time | string | lower}}</AllowPassageOfTime>
                </Time>"""
        )

    def __init__(self, allow_passage_of_time: bool, start_time: int = None):
        self.start_time = start_time
        self.allow_passage_of_time = allow_passage_of_time


# <Weather>clear</Weather>
class WeatherInitialCondition(Handler):
    def to_string(self) -> str:
        return "weather_initial_condition"

    def xml_template(self) -> str:
        return str(
            """<Weather>{{weather | string }}</Weather>"""
        )

    def __init__(self, weather: str):
        self.weather = weather


# <AllowSpawning>false</AllowSpawning>
class SpawningInitialCondition(Handler):
    def to_string(self) -> str:
        return "spawning_initial_condition"

    def xml_template(self) -> str:
        return str(
            """<AllowSpawning>{{allow_spawning | string | lower}}</AllowSpawning>"""
        )

    def __init__(self, allow_spawning: bool):
        self.allow_spawning = allow_spawning
