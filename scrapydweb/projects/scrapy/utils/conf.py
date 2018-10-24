# coding: utf8
try:
    from ConfigParser import SafeConfigParser
except ImportError:
    from configparser import ConfigParser as SafeConfigParser


def get_config(sources):
    """Get Scrapy config file as a SafeConfigParser"""
    # sources = get_sources(use_closest)
    cfg = SafeConfigParser()
    cfg.read(sources)
    return cfg
