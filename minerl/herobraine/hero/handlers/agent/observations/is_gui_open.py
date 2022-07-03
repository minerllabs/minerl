import typing
from typing import Any
from minerl.herobraine.hero import spaces
from minerl.herobraine.hero.handlers.translation import TranslationHandler

class IsGuiOpen(TranslationHandler):
    def __init__(self):
        super().__init__(spaces.Discrete(2))

    def from_hero(self, x: typing.Dict[str, Any]):
        return x["isGuiOpen"]

    def xml_template(self):
        return "<IsGuiOpen/>"

    def to_hero(self, x) -> str:
        raise NotImplementedError("This should not be called")
        # theoretically, this is 
        # return json.dumps[{"isGuiOpen": x}]

    def from_universal(self, x: typing.Dict[str, Any]):
        return x["isGuiOpen"]

    def to_string(self) -> str:
        return "isGuiOpen"
