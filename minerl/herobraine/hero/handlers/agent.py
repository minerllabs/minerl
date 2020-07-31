"""agent.py
Defines miscellaneous agent handlers and behaviour.
"""

# Its important to note that handlers don't have behaviours.
# Minimally, we need something we can embed in XML.
# Then there are SpacedHandlers.


from typing import Iterable, List

import jinja2
from minerl.herobraine.hero.handlers.mixins import SimpleXMLElementMixin
from minerl.herobraine.hero.handler import Handler


class PauseAction(Handler, SimpleXMLElementMixin):
    def to_string(self):
        return "pause"

    @property
    def xml_element(self) -> str:
        return "PauseCommand"


# TODO: Consider making these item list xml's a MIXIN as well!
class AgentQuitFromPosessingItem(Handler):
    TEMPLATE = jinja2.Template("""
        <AgentQuitFromPosessingItem>
            {{% for item in items %}}
                <Item type="{{item}}"/>
            {{% endfor %}}
        </AgentQuitFromPosessingItem>
    """)
    
    def __init__(self, items : Iterable[str]):
        self.items = set(items)

    def to_string(self):
        "quit_from_posessing_item"

    def xml(self) -> str:
        return self.TEMPLATE.render(items=sorted(list(self.items)))

    def __or__(self, other):
        super().__or__(other)
        return AgentQuitFromPosessingItem(
            self.items | other.items
        )

    


        