# coding: utf8
import io
import json
import os
import time

from flask import Response


# http://flask.pocoo.org/snippets/category/authentication/
def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response("<script>alert('FAIL to login: basic auth for ScrapydWeb has been enabled');</script>",
                    401, {'WWW-Authenticate': 'Basic realm="ScrapydWeb Basic Auth Required"'})


def find_scrapydweb_settings_py(filename, path, prevpath=None):
    if path == prevpath:
        return ''
    path = os.path.abspath(path)
    cfgfile = os.path.join(path, filename)
    if os.path.exists(cfgfile):
        return cfgfile
    return find_scrapydweb_settings_py(filename, os.path.dirname(path), path)


def get_pageview_dict(path):
    pageview = 0
    try:
        if not os.path.exists(path):
            with io.open(path, 'w') as f:
                f.write(u'{:.0f}'.format(time.time()))
        else:
            with io.open(path, 'r+') as f:
                if time.time() - int(f.read()) > 3600 * 24 * 7:
                    f.seek(0)
                    f.write(u'{:.0f}'.format(time.time()))
                else:
                    pageview = 1
    except:
        try:
            os.remove(path)
        except:
            pass

    return dict(overview=pageview, dashboard=pageview)


def json_dumps(obj, sort_keys=True):
    return json.dumps(obj, ensure_ascii=False, indent=4, sort_keys=sort_keys)


def printf(value, warn=False):
    prefix = "!!!" if warn else ">>>"
    print("%s %s" % (prefix, value))
