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

SCRAPY_CFG_DICT = dict(
    demo_only_scrapy_cfg='No module named',  # Result from Scrapyd server
    demo_without_scrapy_cfg='scrapy.cfg NOT found',

    scrapy_cfg_no_settings_default='No section: &#39;settings&#39;',
    scrapy_cfg_no_section_settings='File contains no section headers.',
    scrapy_cfg_no_option_default='No option &#39;default&#39; in section: &#39;settings&#39;',
    scrapy_cfg_no_option_default_equal='contains parsing errors',
    scrapy_cfg_no_option_default_value='returned non-zero exit status',

    scrapy_cfg_no_deploy_project='',
    scrapy_cfg_no_section_deploy='',
    scrapy_cfg_no_option_project='',
    scrapy_cfg_no_option_project_equal='contains parsing errors',
    scrapy_cfg_no_option_project_value='',
)


def req(app, client, view='', kws=None, url='', data=None, ins=None, nos=None, jskws=None, jskeys=None,
        location=None, mobileui=False, headers=None, single_scrapyd=False, set_to_second=False):
    if single_scrapyd and len(app.config['SCRAPYD_SERVERS']) > 1:
        SCRAPYD_SERVERS = app.config['SCRAPYD_SERVERS'][:1] if not set_to_second else app.config['SCRAPYD_SERVERS'][1:]
        app.config['SCRAPYD_SERVERS'] = SCRAPYD_SERVERS
        app.config['SCRAPYD_SERVERS_AMOUNT'] = 1

    with app.test_request_context():
        if not url:
            url = url_for(view, **kws)
        if data is not None:
            response = client.post(url, headers=headers, data=data, content_type='multipart/form-data')
        else:
            response = client.get(url, headers=headers)
        text = response.get_data(as_text=True)
        js = {}
        try:
            js = json.loads(text)
        except ValueError:
            pass

        if isinstance(ins, str):
            assert ins in text
        elif isinstance(ins, list):
            for i in ins:
                assert i in text
        elif ins:
            raise TypeError("The argument 'ins' should be either a string or a list")

        if isinstance(nos, str):
            assert nos not in text
        elif isinstance(nos, list):
            for n in nos:
                assert n not in text
        elif nos:
            raise TypeError("The argument 'nos' should be either a string or a list")

        if location:
            try:
                assert response.headers['Location'].endswith(location)
            except AssertionError:
                assert location in response.headers['Location']

        if jskws:
            for k, v in jskws.items():
                try:
                    assert js[k] == v
                except AssertionError:
                    # v is an element of js[k] or a substring of js[k]
                    assert v in js[k]

        if jskeys:
            if isinstance(jskeys, str):
                assert jskeys in js.keys()
            elif isinstance(jskeys, list):
                for k in jskeys:
                    assert k in js.keys()
            elif jskeys:
                raise TypeError("The argument 'jskeys' should be either a string or a list")

        if mobileui:
            assert 'Desktop version' in text
        else:
            assert 'Desktop version' not in text

        return text, js


def req_single_scrapyd(*args, **kwargs):
    kwargs.update({'single_scrapyd': True})
    return req(*args, **kwargs)


def sleep(seconds=10):
    time.sleep(seconds)


def get_text(response):
    return response.get_data(as_text=True)


def load_json(response):
    # js = response.get_json()
    return json.loads(get_text(response))


def set_single_scrapyd(app, set_second=False):
    SCRAPYD_SERVERS = app.config['SCRAPYD_SERVERS'][:1] if not set_second else app.config['SCRAPYD_SERVERS'][1:]
    app.config['SCRAPYD_SERVERS'] = SCRAPYD_SERVERS
    app.config['SCRAPYD_SERVERS_AMOUNT'] = 1


def upload_file_deploy(app, client, filename, project, multinode=False,
                       fail=False, redirect_project=None, alert=None):
    data = {
        'project': project,
        'version': VERSION,
        'file': (os.path.join(CWD, u'data/%s' % filename), filename)
    }
    if multinode:
        data.update({'1': 'on', '2': 'on', 'checked_amount': '2'})
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
