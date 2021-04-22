# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import os
import pathlib
from minerl.data.util.constants import touch

MODULE_PATH = pathlib.Path(__file__).parent.absolute()
BLACKLIST_DIR_PATH = MODULE_PATH / 'assets' / 'blacklist'


class Blacklist:

    def __init__(self, blacklist_dir=BLACKLIST_DIR_PATH):
        self.file_name = blacklist_dir
        os.makedirs(self.file_name, exist_ok=True)

    def add(self, other):
        touch(os.path.join(self.file_name, other))

    def __contains__(self, item):
        return item in os.listdir(self.file_name)
