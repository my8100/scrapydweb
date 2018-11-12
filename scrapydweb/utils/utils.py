# coding: utf8
import os
import json

from flask import Response


def printf(value, warn=False):
    prefix = "!!!" if warn else ">>>"
    print("%s %s" % (prefix, value))


def json_dumps(obj, sort_keys=True):
    return json.dumps(obj, ensure_ascii=False, indent=4, sort_keys=sort_keys)


def find_scrapydweb_settings_py(filename, path, prevpath=None):
    if path == prevpath:
        return ''
    path = os.path.abspath(path)
    cfgfile = os.path.join(path, filename)
    if os.path.exists(cfgfile):
        return cfgfile
    return find_scrapydweb_settings_py(filename, os.path.dirname(path), path)


# http://flask.pocoo.org/snippets/category/authentication/
def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response("<script>alert('FAIL to login: basic auth for ScrapydWeb has been enabled');</script>",
                    401, {'WWW-Authenticate': 'Basic realm="ScrapydWeb Basic Auth Required"'})
