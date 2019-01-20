# coding: utf8
import json
import locale
import io
import os
import platform
from shutil import rmtree, copy
import sys
import time
import zipfile

from flask import url_for

from logparser import __version__ as logparser_version


class Constant(object):
    PROJECT = 'ScrapydWeb_demo'
    VERSION = '2018-01-01T01_01_01'
    SPIDER = 'test'
    JOBID = '2018-01-01T01_01_02'

    FAKE_PROJECT = 'FAKE_PROJECT'
    FAKE_VERSION = 'FAKE_VERSION'
    FAKE_SPIDER = 'FAKE_SPIDER'
    FAKE_JOBID = 'FAKE_JOBID'

    NA = 'N/A'
    OK = 'ok'
    ERROR = 'error'
    DEFAULT_LATEST_VERSION = 'default: the latest version'
    DEMO_LOG = 'ScrapydWeb_demo.log'
    DEMO_JSON = 'ScrapydWeb_demo.json'
    DEMO_UNFINISHED_LOG = 'ScrapydWeb_demo_unfinished.log'
    DEMO_UNFINISHED_JSON = 'ScrapydWeb_demo_unfinished.json'

    CWD = os.path.dirname(os.path.abspath(__file__))
    LOGPARSER_VERSION = logparser_version

    # default UA: werkzeug/0.14.1
    HEADERS_DICT = dict(
        Chrome={'User-Agent': 'Chrome'},
        iPad={'User-Agent': 'iPad'},
        iPhone={'User-Agent': 'iPhone'},
        Android={'User-Agent': 'Android'},
        IE={'User-Agent': 'msie'},
        EDGE={'User-Agent': 'EDGE'},
    )

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

    VIEW_TITLE_MAP = {
        'overview': 'Monitor and control',
        'dashboard': 'Get the list of pending',

        'deploy.deploy': 'Add a version to a project',
        'schedule.schedule': 'Schedule a spider run',
        'manage': 'Get the list of projects uploaded',

        'logs': 'Directory listing for /logs/',
        'parse.upload': 'Upload a scrapy logfile to parse',
        'settings': 'default_settings.py'
    }

    (_language_code, _encoding) = locale.getdefaultlocale()
    WINDOWS_NOT_CP936 = True if platform.system() == 'Windows' and _encoding != 'cp936' else False


cst = Constant()


def get_text(response):
    return response.get_data(as_text=True)


def req(app, client, view='', kws=None, url='', data=None, ins=None, nos=None, jskws=None, jskeys=None,
        location=None, mobileui=False, headers=None, single_scrapyd=False, set_to_second=False):
    if single_scrapyd:
        set_single_scrapyd(app, set_to_second)

    with app.test_request_context():
        if not url:
            url = url_for(view, **kws)
        if data is not None:
            response = client.post(url, headers=headers, data=data, content_type='multipart/form-data')
        else:
            response = client.get(url, headers=headers)
        # with io.open('response.html', 'wb') as f:
            # f.write(response.data)
        text = get_text(response)
        # print(text)
        js = {}
        try:
            # js = response.get_json()
            js = json.loads(text)
        except ValueError:  # includes JSONDecodeError
            pass
        # print(js)
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


def set_env(custom_settings):
    if not custom_settings.get('SCRAPYD_LOGS_DIR', ''):
        custom_settings['SCRAPYD_LOGS_DIR'] = os.path.join(os.path.expanduser('~'), 'logs')
        print("Set SCRAPYD_LOGS_DIR to: %s" % custom_settings['SCRAPYD_LOGS_DIR'])
    scrapyd_logs_dir = custom_settings['SCRAPYD_LOGS_DIR']
    if not os.path.isdir(scrapyd_logs_dir):
        sys.exit("custom_settings['SCRAPYD_LOGS_DIR'] not found: %s" % repr(scrapyd_logs_dir))

    data_folder = os.path.join(cst.CWD, 'data')
    if os.path.isdir(data_folder):
        rmtree(data_folder, ignore_errors=True)
    with zipfile.ZipFile(os.path.join(cst.CWD, 'data.zip'), 'r') as f:
        f.extractall(cst.CWD)

    project_path = os.path.join(scrapyd_logs_dir, cst.PROJECT)
    spider_path = os.path.join(project_path, cst.SPIDER)
    for path in [project_path, spider_path]:
        if not os.path.isdir(path):
            os.mkdir(path)
    src = os.path.join(cst.CWD, 'data', cst.DEMO_LOG)
    for filename in [cst.DEMO_LOG, cst.DEMO_UNFINISHED_LOG]:
        dst = os.path.join(spider_path, filename)
        copy(src, dst)
        print("Copied to %s from %s" % (dst, src))
        # 'finish_reason': 'finished',
        if filename == cst.DEMO_UNFINISHED_LOG:
            with io.open(dst, 'r+', encoding='utf-8') as f:
                content = f.read()
                f.seek(0)
                f.write(content.replace("'finish_reason'", ''))
            print("Remove 'finish_reason' in %s" % dst)
    stats_json_path = os.path.join(scrapyd_logs_dir, 'stats.json')
    demo_json_path = os.path.join(spider_path, cst.DEMO_JSON)
    demo_unfinished_json_path = os.path.join(spider_path, cst.DEMO_UNFINISHED_JSON)
    custom_settings['STATS_JSON_PATH'] = stats_json_path
    custom_settings['DEMO_JSON_PATH'] = demo_json_path
    for path in [stats_json_path, demo_json_path, demo_unfinished_json_path]:
        if os.path.exists(path):
            os.remove(path)
            print("Deleted: %s" % path)


def set_single_scrapyd(app, set_to_second=False):
    if len(app.config['SCRAPYD_SERVERS']) > 1:
        index = -1 if set_to_second else 0
        app.config['SCRAPYD_SERVERS'] = [app.config['SCRAPYD_SERVERS'][index]]
        app.config['SCRAPYD_SERVERS_AUTHS'] = [app.config['SCRAPYD_SERVERS_AUTHS'][index]]
        app.config['SCRAPYD_SERVERS_AMOUNT'] = 1


def sleep(seconds=10):
    time.sleep(seconds)


def switch_scrapyd(app):
    if len(app.config['SCRAPYD_SERVERS']) > 1:
        app.config['SCRAPYD_SERVERS'] = app.config['SCRAPYD_SERVERS'][::-1]
        app.config['SCRAPYD_SERVERS_AUTHS'] = app.config['SCRAPYD_SERVERS_AUTHS'][::-1]


def upload_file_deploy(app, client, filename, project, multinode=False,
                       fail=False, redirect_project=None, alert=None):
    data = {
        'project': project,
        'version': cst.VERSION,
        'file': (os.path.join(cst.CWD, u'data/%s' % filename), filename)
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
            url_redirect = url_for('schedule.schedule', node=1, project=redirect_project, version=cst.VERSION)
            if multinode:
                assert response.status_code == 200 and "deploy results - ScrapydWeb" in text and url_redirect in text
            else:
                assert response.status_code == 302 and response.headers['Location'].endswith(url_redirect)

        if alert:
            assert alert in text
