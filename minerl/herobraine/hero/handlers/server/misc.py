# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton


import jinja2
from minerl.herobraine.hero.handler import Handler


# TODO: THIS SHOULD ACTUALLY BE AN INITIAL CONDITONS OR AN AGENT
# START HANDLER :\ HENCE THE MISC CLASSIFCIATION.
class RandomizedStartDecorator(Handler):
    def to_string(self) -> str:
        return "randomized_start_decorator"

    def xml_template(self) -> str:
        return str(
            """<RandomizedStartDecorator/>"""
        )
