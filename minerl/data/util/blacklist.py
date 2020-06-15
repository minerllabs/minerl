import os
from filelock import FileLock


class Blacklist(set):

    def __init__(self):
        self.file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'blacklist.txt'))
        super().__init__(open(self.file_name).readlines())
        self.initial_list = list(self)

    def add(self, other):
        super().add(other)
        self.save()

    def save(self):
        with FileLock(self.file_name) as flock:
            disk = set(open(self.file_name).readlines())
            self.union(disk)
            out_file = open(self.file_name, 'w')
            out_file.writelines(list(self))
