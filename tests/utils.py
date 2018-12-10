# coding: utf8
import os
import time
import json
import platform
import locale

from flask import url_for

from scrapydweb.vars import DEFAULT_LATEST_VERSION


CWD = os.path.dirname(os.path.abspath(__file__))

# default UA: werkzeug/0.14.1
HEADERS_DICT = dict(
    Chrome={'User-Agent': 'Chrome'},
    iPad={'User-Agent': 'iPad'},
    iPhone={'User-Agent': 'iPhone'},
    Android={'User-Agent': 'Android'},
    IE={'User-Agent': 'msie'},
    EDGE={'User-Agent': 'EDGE'},
)

DEFAULT_LATEST_VERSION = DEFAULT_LATEST_VERSION
PROJECT = 'ScrapydWeb-demo'
VERSION = '2018-01-01T01_01_01'
SPIDER = 'test'
JOBID = '2018-01-01T01_01_02'

FAKE_PROJECT = 'FAKE_PROJECT'
FAKE_VERSION = 'FAKE_VERSION'
FAKE_SPIDER = 'FAKE_SPIDER'
FAKE_JOBID = 'FAKE_JOBID'

OK = 'ok'
ERROR = 'error'

(_language_code, _encoding) = locale.getdefaultlocale()
WINDOWS_NOT_CP936 = True if platform.system() == 'Windows' and _encoding != 'cp936' else False

VIEW_TITLE_MAP = {
    'overview': 'Monitor and control',
    'dashboard': 'Get the list of pending',

    'deploy.deploy': 'Add a version to a project',
    'schedule.schedule': 'Schedule a spider run',
    'manage': 'Get the list of projects uploaded',

    'logs': 'Directory listing for /logs/',
    'parse.upload': 'Upload a scrapy log file to parse',
    'settings': 'default_settings.py'
}


def sleep(seconds=10):
    time.sleep(seconds)


def get_text(response):
    return response.get_data(as_text=True)


def load_json(response):
    return json.loads(get_text(response))


def is_mobileui(response):
    return 'Desktop version' in get_text(response)


def upload_file_deploy(app, client, filename, project, multinode=False,
                       fail=False, redirect_project=None, alert=None):
    data = {
        'project': project,
        'version': VERSION,
        'file': (os.path.join(CWD, u'data/%s' % filename), filename)
    }
    if multinode:
        data.update({'checked_amount': '2', '1': 'on', '2': 'on'})
    with app.test_request_context():
        url = url_for('deploy.upload', node=1)
        response = client.post(url, content_type='multipart/form-data', data=data)
        text = get_text(response)
        if fail:
            assert response.status_code == 200 and "fail - ScrapydWeb" in text
        else:
            url_redirect = url_for('schedule.schedule', node=1, project=redirect_project, version=VERSION)
            if multinode:
                assert response.status_code == 200 and "deploy results - ScrapydWeb" in text and url_redirect in text
            else:
                assert response.status_code == 302 and response.headers['Location'].endswith(url_redirect)

        if alert:
            assert alert in text


def set_single_scrapyd(app, set_second=False):
    SCRAPYD_SERVERS = app.config['SCRAPYD_SERVERS'][:1] if not set_second else app.config['SCRAPYD_SERVERS'][1:]
    app.config['SCRAPYD_SERVERS'] = SCRAPYD_SERVERS
    app.config['SCRAPYD_SERVERS_AMOUNT'] = 1
