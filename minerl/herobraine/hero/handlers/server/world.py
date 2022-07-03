# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

"""Handlers relating to world generation."""

import jinja2
from minerl.herobraine.hero.handler import Handler


class DefaultWorldGenerator(Handler):
    def to_string(self) -> str:
        return "default_world_generator"

    def xml_template(self) -> str:
        return str(
            """<DefaultWorldGenerator
                forceReset="{{force_reset | string | lower}}"
                generatorOptions='{{generator_options}}'/>
            """
        )

    def __init__(self, force_reset=True, generator_options: str = "{}"):
        """Generates a world using minecraft procedural generation.

        Args:
            force_reset (bool, optional): If the world should be reset every episode.. Defaults to True.
            generator_options: A JSON object specifying parameters to the procedural generator.
        """
        self.force_reset = force_reset
        self.generator_options = generator_options


class FileWorldGenerator(Handler):
    """Generates a world from a file."""

    def to_string(self) -> str:
        return "file_world_generator"

    def xml_template(self) -> str:
        return str(
            """<FileWorldGenerator
                destroyAfterUse = "{{destroy_after_use | string | lower}}"
                src = "{{filename}}" />
            """
        )

    def __init__(self, filename: str, destroy_after_use: bool = True):
        self.filename = filename
        self.destroy_after_use = destroy_after_use


#  <FlatWorldGenerator forceReset="true"/>
class FlatWorldGenerator(Handler):
    """Generates a world that is a flat landscape."""

    def to_string(self) -> str:
        return "flat_world_generator"

    def xml_template(self) -> str:
        return str(
            """<FlatWorldGenerator
                forceReset="{{force_reset | string | lower}}"
                generatorString="{{generatorString}}" />
            """
        )

    def __init__(self, force_reset: bool = True, generatorString: str =""):
        self.force_reset = force_reset
        self.generatorString = generatorString



#  <BiomeGenerator forceReset="true" biome="3"/>
class BiomeGenerator(Handler):
    def to_string(self) -> str:
        return "biome_generator"

    def xml_template(self) -> str:
        return str(
            """<BiomeGenerator
                forceReset="{{force_reset | string | lower}}"
                biome="{{biome_id}}" />
            """
        )

    def __init__(self, biome_id: int, force_reset: bool = True):
        self.biome_id = biome_id
        self.force_reset = force_reset


class DrawingDecorator(Handler):
    def __init__(self, to_draw: str):
        self.to_draw = to_draw

    def xml_template(self) -> str:
        tmp = """<DrawingDecorator>{{to_draw}}</DrawingDecorator>"""
        return tmp

    def to_string(self) -> str:
        return "drawing_decorator"

class RemoteServer(Handler):
    def __init__(self, address: str):
        self.address = address

    def xml_template(self) -> str:
        address = self.address
        if callable(address):
            address = address()
        if not isinstance(address, str):
            raise ValueError(f"address should be a string (provided {address})")
        return f"<RemoteServer>{address}</RemoteServer>"

    def to_string(self) -> str:
        return "remote_server"
