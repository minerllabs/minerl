"""These handlers allow episode termination based on server conditions (e.g. time passed)

When used to create a Gym environment, they should be passed to :code:`create_server_quit_producers`
"""
# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton


import jinja2
from minerl.herobraine.hero.handler import Handler


class ServerQuitFromTimeUp(Handler):
    """ 
    Forces the server to quit after a certain time_limit_ms
    also specifies a description parameter for the xml.
    
    Example usage

    .. code-block:: python

        ServerQuitFromTimeUp(50000)
    """

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


class ServerQuitWhenAnyAgentFinishes(Handler):
    """ 
    Forces the server to quit if any of the agents involved quits.
    Has no parameters.
    
    Example usage:

    .. code-block:: python
    
        ServerQuitWhenAnyAgentFinishes()
    """

    def to_string(self) -> str:
        return "server_quit_when_any_agent_finishes"

    def xml_template(self) -> str:
        return str(
            """<ServerQuitWhenAnyAgentFinishes/>
            """
        )
