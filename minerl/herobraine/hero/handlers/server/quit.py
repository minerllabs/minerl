

import jinja2
from minerl.herobraine.hero.handler import Handler





class ServerQuitFromTimeUp(Handler):
    """ Forces the server to quit after a certain time_limit_ms
    also specifies a description parameter for the xml.""" 

    def to_string(self) -> str:
        return "server_quit_after_time_up"

    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<ServerQuitFromTimeUp 
                    timeLimitMs="{{str(time_limit_ms)}}"
                    description="{{description}}"/>
            """
        )

    def __init__(self, time_limit_ms, description="out_of_time"):
        self.time_limit_ms = time_limit_ms
        self.description = description


class ServerQuitWhenAnyAgentFinishes(Handler):
    """ Forces the server to quit if any of the agents involved quits.
    Has no parameters."""

    def to_string(self) -> str:
         return "server_quit_when_any_agent_finishes"

    def xml_template(self) -> jinja2.Template:
        return jinja2.Template(
            """<ServerQuitWhenAnyAgentFinishes/>
            """
        )
