# coding: utf8
import os
import tempfile
import zipfile
import tarfile
from shutil import copyfile, rmtree
from collections import OrderedDict

from flask import current_app as app

from .scrapyd_deploy import _build_egg


def uncompress_to_tmpdir(filepath):
    app.logger.debug("Uncompress %s" % filepath)
    tmpdir = tempfile.mkdtemp(prefix="scrapydweb-uncompress-")
    if(filepath.endswith('zip')):
        zip = zipfile.ZipFile(filepath, 'r')
        zip.extractall(tmpdir)
        zip.close()
    else: # 'tar' 'tar.gz'
        tar = tarfile.open(filepath, 'r') # Open for reading with transparent compression (recommended).
        tar.extractall(tmpdir)
        tar.close()

    app.logger.debug("Uncompress to %s" % tmpdir)
    return tmpdir


def search_scrapy_cfg_path(search_path):
    paths = []
    for dirpath, dirnames, filenames in os.walk(search_path):
        paths.append(os.path.abspath(dirpath))
        scrapy_cfg_path = os.path.abspath(os.path.join(dirpath, 'scrapy.cfg'))
        if os.path.exists(scrapy_cfg_path):
            app.logger.debug("scrapy_cfg_path: %s" % scrapy_cfg_path)
            return (scrapy_cfg_path, paths)

    app.logger.error("scrapy.cfg NOT found within %s " % search_path)
    return ('', paths)


def build_egg(scrapy_cfg_path, eggname, eggpath):
    egg, tmpdir = _build_egg(scrapy_cfg_path)
    copyfile(egg, os.path.join(os.path.dirname(scrapy_cfg_path), eggname))
    copyfile(egg, eggpath)
    rmtree(tmpdir)
    app.logger.debug("egg file saved to: %s" % eggpath)
    

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
