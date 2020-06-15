import os


class Blacklist(set):

    def __init__(self):
        self.file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'blacklist.txt'))
        super().__init__(open(self.file_name).readlines())

    def add(self, other):
        super().add(other)
        self.save()

    def remove(self, element) -> None:
        super().remove(element)
        self.save()

    def save(self):
        out_file = open(self.file_name, 'w')
        out_file.writelines(list(self))
