# coding: utf-8
from collections import OrderedDict
import errno
import os


class Slot:
    def __init__(self, limit_egg=10, limit_data=10):
        self.limit_egg = limit_egg
        self.limit_data = limit_data
        self._egg = OrderedDict()
        self._data = OrderedDict()

    @property
    def egg(self):
        return self._egg

    @property
    def data(self):
        return self._data

    def add_egg(self, key, value):
        self._egg[key] = value
        if len(self._egg) > self.limit_egg:
            self._egg.popitem(last=False)

    def add_data(self, key, value):
        self._data[key] = value
        if len(self._data) > self.limit_data:
            self._data.popitem(last=False)


slot = Slot()


# https://stackoverflow.com/a/600612/10517783
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as err:  # Python >2.5
        if err.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
