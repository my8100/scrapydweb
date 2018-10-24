# coding: utf8
import os
import re
from collections import defaultdict

from flask import Blueprint, render_template
from flask import current_app as app

from ..vars import DEMO_PROJECTS_PATH, ALLOWED_SCRAPYD_LOG_EXTENSIONS
from ..utils import json_dumps


CWD = os.path.dirname(os.path.abspath(__file__))

bp = Blueprint('settings', __name__, url_prefix='/')


def protect(string):
    length = len(string)
    if length == 0:
        return string
    elif length < 3:
        return re.sub(r'^.', '*', string)
    else:
        return re.sub(r'^.(.*?).$', r'*\1*', string)


@bp.route('/<int:node>/settings/')
def settings(node):
    config = app.config
    kwargs = {}

    # User settings
    kwargs['default_settings_py'] = os.path.join(os.path.dirname(CWD), 'default_settings.py')

    # ScrapydWeb
    kwargs['scrapydweb_server'] = json_dumps({
        'SCRAPYDWEB_BIND': config.get('SCRAPYDWEB_BIND', '127.0.0.1'),
        'SCRAPYDWEB_PORT': config.get('SCRAPYDWEB_PORT', 5000)
    })
    kwargs['scrapydweb_auth'] = json_dumps({
        'USERNAME': protect(config.get('USERNAME', '')),
        'PASSWORD': protect(config.get('PASSWORD', ''))
    })

    # Scrapy
    kwargs['SCRAPY_PROJECTS_DIR'] = config.get('SCRAPY_PROJECTS_DIR', '') or DEMO_PROJECTS_PATH

    # Scrapyd
    SCRAPYD_SERVERS_GROUPS = config.get('SCRAPYD_SERVERS_GROUPS', [''])
    SCRAPYD_SERVERS = config.get('SCRAPYD_SERVERS', ['127.0.0.1'])
    SCRAPYD_SERVERS_AUTHS = config.get('SCRAPYD_SERVERS_AUTHS', [None])
    servers = defaultdict(list)
    for group, server, auth in zip(SCRAPYD_SERVERS_GROUPS, SCRAPYD_SERVERS, SCRAPYD_SERVERS_AUTHS):
        servers[group].append('%s:%s@%s' % (protect(auth[0]), protect(auth[1]), server) if auth else server)

    kwargs['servers'] = json_dumps(servers)
    kwargs['SCRAPYD_LOGS_DIR'] = config.get('SCRAPYD_LOGS_DIR', '') or "''"
    kwargs['SCRAPYD_LOG_EXTENSIONS'] = config.get('SCRAPYD_LOG_EXTENSIONS', []) or ALLOWED_SCRAPYD_LOG_EXTENSIONS

    # Page display
    kwargs['DEBUG'] = config.get('DEBUG', False)
    kwargs['SHOW_SCRAPYD_ITEMS'] = config.get('SHOW_SCRAPYD_ITEMS', True)
    kwargs['SHOW_DASHBOARD_JOB_COLUMN'] = config.get('SHOW_DASHBOARD_JOB_COLUMN', False)
    kwargs['DASHBORAD_RELOAD_INTERVAL'] = config.get('DASHBORAD_RELOAD_INTERVAL', 300)
    kwargs['DAEMONSTATUS_REFRESH_INTERVAL'] = config.get('DAEMONSTATUS_REFRESH_INTERVAL', 10)

    # Html caching
    kwargs['DISABLE_CACHE'] = config.get('DISABLE_CACHE', False)
    kwargs['DELETE_CACHE'] = config.get('DELETE_CACHE', False)
    kwargs['CACHE_ROUND_INTERVAL'] = config.get('CACHE_ROUND_INTERVAL', 300)
    kwargs['CACHE_REQUEST_INTERVAL'] = config.get('CACHE_REQUEST_INTERVAL', 10)


    return render_template('scrapydweb/settings.html', node=node, **kwargs)
