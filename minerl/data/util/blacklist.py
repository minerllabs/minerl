import os
import warnings
from filelock import FileLock


class Blacklist(set):

    def __init__(self):
        self.file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'blacklist.txt'))
        super().__init__([elem[:-1] for elem in open(self.file_name)])

    def add(self, other):
        super().add(other)
        self.save()

    def save(self):
        with FileLock(self.file_name):
            disk = Blacklist()
            warnings.warn(str(disk))

            warnings.warn(str(list(disk)))
            self.union(disk)
            warnings.warn(str(self))

            out_file = open(self.file_name, 'w')
            out_file.writelines([elem + '\n' for elem in list(self)])
