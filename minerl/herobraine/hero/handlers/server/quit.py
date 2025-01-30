# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton


import jinja2
from minerl.herobraine.hero.handler import Handler


class ServerQuitFromTimeUp(Handler):
    """ Forces the server to quit after a certain time_limit_ms
    also specifies a description parameter for the xml."""

    def to_string(self) -> str:
        return "server_quit_after_time_up"

    def xml_template(self) -> str:
        return str(
            """<ServerQuitFromTimeUp 
                    timeLimitMs="{{ time_limit_ms | string }}"
                    description="{{description}}"/>
            """
        )

    def __init__(self, time_limit_ms: int, description="out_of_time"):
        self.time_limit_ms = time_limit_ms
        self.description = description

class ServerQuitFromDeath(Handler):
    """ Forces the server to quit after a certain time_limit_ms
    also specifies a description parameter for the xml."""

    def to_string(self) -> str:
        return "server_quit_from_death"

    def xml_template(self) -> str:
        return str(
            """<ServerQuitFromTimeUp 
                    quitWhenAnyDead="{{quit_when_any_agent_dies}}"/>
            """
        )

    def __init__(self, quit_when_any_agent_dies: bool):
        self.quit_when_any_agent_dies = quit_when_any_agent_dies


class ServerQuitWhenAnyAgentFinishes(Handler):
    """ Forces the server to quit if any of the agents involved quits.
    Has no parameters."""

    def to_string(self) -> str:
        return "server_quit_when_any_agent_finishes"

    def xml_template(self) -> str:
        return str(
            """<ServerQuitWhenAnyAgentFinishes/>
            """
        )
