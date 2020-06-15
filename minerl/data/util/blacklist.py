import os
from minerl.data.util.constants import touch


class Blacklist:

    def __init__(self):
        self.file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'blacklist'))
        os.makedirs(self.file_name, exist_ok=True)
    def add(self, other):
        touch(os.path.join(self.file_name, other))

    def __contains__(self, item):
        return item in os.listdir(self.file_name)