import os
from minerl.data.util.constants import touch


class Blacklist:

    def __init__(self):
        self.file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'blacklist'))

    def add(self, other):
        touch(os.path.join(self.file_name, other))

    def __contains__(self, item):
        os.path.exists(os.path.join(self.file_name, item))

