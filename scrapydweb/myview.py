# coding: utf8
import time
import re
import json
import logging

import requests
from requests.adapters import HTTPAdapter
from requests.auth import _basic_auth_str
from flask import request, url_for, g
from flask import current_app as app
from flask.views import View

from .vars import ALLOWED_SCRAPYD_LOG_EXTENSIONS, DEMO_PROJECTS_PATH, EMAIL_TRIGGER_KEYS
from .utils.utils import json_dumps


session = requests.Session()
session.mount('http://', HTTPAdapter(pool_connections=1000, pool_maxsize=1000))
session.mount('https://', HTTPAdapter(pool_connections=1000, pool_maxsize=1000))


class MyView(View):
    methods = ['GET', 'POST']

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)

        # System
        self.DEBUG = app.config.get('DEBUG', False)
        self.VERBOSE = app.config.get('VERBOSE', False)

        _level = logging.DEBUG if self.VERBOSE else logging.WARNING
        self.logger.setLevel(_level)
        logging.getLogger("requests").setLevel(_level)
        logging.getLogger("urllib3").setLevel(_level)

        if request.args:
            self.logger.debug('request.args\n%s' % self.json_dumps(request.args))
        if request.form:
            self.logger.debug('request.form\n%s' % self.json_dumps(request.form))
        if request.files:
            self.logger.debug('request.files\n\n    %s\n' % request.files)

        # ScrapydWeb
        self.SCRAPYDWEB_BIND = app.config.get('SCRAPYDWEB_BIND', '0.0.0.0')
        self.SCRAPYDWEB_PORT = app.config.get('SCRAPYDWEB_PORT', 5000)

        self.ENABLE_AUTH = app.config.get('ENABLE_AUTH', False)
        self.USERNAME = app.config.get('USERNAME', '')
        self.PASSWORD = app.config.get('PASSWORD', '')

        # Scrapy
        self.SCRAPY_PROJECTS_DIR = app.config.get('SCRAPY_PROJECTS_DIR', '') or DEMO_PROJECTS_PATH

        # Scrapyd
        self.SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800']
        self.SCRAPYD_SERVERS_AMOUNT = len(self.SCRAPYD_SERVERS)
        self.SCRAPYD_SERVERS_GROUPS = app.config.get('SCRAPYD_SERVERS_GROUPS', []) or ['']
        self.SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', []) or [None]

        self.SCRAPYD_LOGS_DIR = app.config.get('SCRAPYD_LOGS_DIR', '')
        self.SCRAPYD_LOG_EXTENSIONS = (app.config.get('SCRAPYD_LOG_EXTENSIONS', [])
                                       or ALLOWED_SCRAPYD_LOG_EXTENSIONS)

        # Page Display
        self.SHOW_SCRAPYD_ITEMS = app.config.get('SHOW_SCRAPYD_ITEMS', True)
        self.SHOW_DASHBOARD_JOB_COLUMN = app.config.get('SHOW_DASHBOARD_JOB_COLUMN', False)
        self.DASHBOARD_RELOAD_INTERVAL = app.config.get('DASHBOARD_RELOAD_INTERVAL', 300)
        self.DAEMONSTATUS_REFRESH_INTERVAL = app.config.get('DAEMONSTATUS_REFRESH_INTERVAL', 10)
        self.LAST_LOG_ALERT_SECONDS = app.config.get('LAST_LOG_ALERT_SECONDS', 60)  # Not in default_settings.py

        # HTML Caching
        self.ENABLE_CACHE = app.config.get('ENABLE_CACHE', True)
        self.CACHE_ROUND_INTERVAL = app.config.get('CACHE_ROUND_INTERVAL', 300)
        self.CACHE_REQUEST_INTERVAL = app.config.get('CACHE_REQUEST_INTERVAL', 10)
        self.DELETE_CACHE = app.config.get('DELETE_CACHE', False)

        # Email Notice
        self.ENABLE_EMAIL = app.config.get('ENABLE_EMAIL', False)
        self.SMTP_SERVER = app.config.get('SMTP_SERVER', '')
        self.SMTP_PORT = app.config.get('SMTP_PORT', 0)
        self.SMTP_OVER_SSL = app.config.get('SMTP_OVER_SSL', False)
        self.SMTP_CONNECTION_TIMEOUT = app.config.get('SMTP_CONNECTION_TIMEOUT', 10)
        self.FROM_ADDR = app.config.get('FROM_ADDR', '')
        self.EMAIL_PASSWORD = app.config.get('EMAIL_PASSWORD', '')
        self.TO_ADDRS = app.config.get('TO_ADDRS', [])

        self.EMAIL_KWARGS = dict(
            smtp_server=self.SMTP_SERVER,
            smtp_port=self.SMTP_PORT,
            smtp_over_ssl=self.SMTP_OVER_SSL,
            smtp_connection_timeout=self.SMTP_CONNECTION_TIMEOUT,
            from_addr=self.FROM_ADDR,
            email_password=self.EMAIL_PASSWORD,
            to_addrs=self.TO_ADDRS,
            subject='subject',
            content='content'
        )

        self.EMAIL_WORKING_DAYS = app.config.get('EMAIL_WORKING_DAYS', [])
        self.EMAIL_WORKING_HOURS = app.config.get('EMAIL_WORKING_HOURS', [])
        self.ON_JOB_RUNNING_INTERVAL = app.config.get('ON_JOB_RUNNING_INTERVAL', 0)
        self.ON_JOB_FINISHED = app.config.get('ON_JOB_FINISHED', False)
        # ['CRITICAL', 'ERROR', 'WARNING', 'REDIRECT', 'RETRY', 'IGNORE']
        for key in EMAIL_TRIGGER_KEYS:
            setattr(self, 'LOG_%s_THRESHOLD' % key, app.config.get('LOG_%s_THRESHOLD' % key, 0))
            setattr(self, 'LOG_%s_TRIGGER_STOP' % key, app.config.get('LOG_%s_TRIGGER_STOP' % key, False))
            setattr(self, 'LOG_%s_TRIGGER_FORCESTOP' % key, app.config.get('LOG_%s_TRIGGER_FORCESTOP' % key, False))

        # Other attributes NOT from config
        self.view_args = request.view_args
        self.node = self.view_args['node']
        assert 0 < self.node <= self.SCRAPYD_SERVERS_AMOUNT, \
            'node index error: %s, which should be between 1 and %s' % (self.node, self.SCRAPYD_SERVERS_AMOUNT)
        self.SCRAPYD_SERVER = self.SCRAPYD_SERVERS[self.node - 1]
        self.GROUP = self.SCRAPYD_SERVERS_GROUPS[self.node - 1]
        self.AUTH = self.SCRAPYD_SERVERS_AUTHS[self.node - 1]

        ua = request.headers.get('User-Agent', '')
        m_mobile = re.search(r'Android|webOS|iPad|iPhone|iPod|BlackBerry|IEMobile|Opera Mini', ua, re.I)
        self.IS_MOBILE = True if m_mobile else False

        m_ipad = re.search(r'iPad', ua, re.I)
        self.IS_IPAD = True if m_ipad else False

        # http://werkzeug.pocoo.org/docs/0.14/utils/#module-werkzeug.useragents
        # /site-packages/werkzeug/useragents.py
        browser = request.user_agent.browser or ''  # lib requests GET: None
        m_edge = re.search(r'Edge', ua, re.I)
        self.IS_IE_EDGE = True if (browser == 'msie' or m_edge) else False

        self.IS_MOBILEUI = True if request.args.get('ui', '') == 'mobile' else False
        self.UI = 'mobile' if self.IS_MOBILEUI else None
        self.GET = True if request.method == 'GET' else False
        self.POST = True if request.method == 'POST' else False

        self.FEATURES = ''
        self.FEATURES += 'A' if self.ENABLE_AUTH else '-'
        self.FEATURES += 'C' if self.ENABLE_CACHE else '-'
        self.FEATURES += 'D' if self.SCRAPY_PROJECTS_DIR != DEMO_PROJECTS_PATH else '-'
        self.FEATURES += 'E' if self.ENABLE_EMAIL else '-'
        self.FEATURES += 'M' if self.IS_MOBILEUI else '-'
        self.FEATURES += 'P' if self.IS_MOBILE else '-'

        # In log.py: pass self.IS_MOBILE to render_template() to override g.IS_MOBILE
        g.IS_MOBILE = self.IS_MOBILE  # lifetime: every single request
        self.update_g()

        self.template_fail = 'scrapydweb/fail_mobileui.html' if self.IS_MOBILEUI else 'scrapydweb/fail.html'

    def update_g(self):
        # For base.html and base_mobileui.html
        # url_menu_XXX might be update by caching subprocess, use update_g() instead of inject_variable()
        g.url_menu_overview = url_for('overview', node=self.node)
        g.url_menu_dashboard = url_for('dashboard', node=self.node)
        g.url_menu_deploy = url_for('deploy.deploy', node=self.node)
        g.url_menu_schedule = url_for('schedule.schedule', node=self.node)
        g.url_menu_manage = url_for('manage', node=self.node)
        g.url_menu_items = url_for('items', node=self.node)
        g.url_menu_logs = url_for('logs', node=self.node)
        g.url_menu_parse = url_for('parse.upload', node=self.node)
        g.url_menu_settings = url_for('settings', node=self.node)
        g.url_menu_mobileui = url_for('index', node=self.node, ui='mobile')

        g.url_daemonstatus = url_for('api', node=self.node, opt='daemonstatus')
        # In log.py: pass url_dashboard_list to render_template() to override g.url_dashboard_list
        g.url_dashboard_list = [url_for('dashboard', node=n, ui=self.UI)
                                for n in range(1, self.SCRAPYD_SERVERS_AMOUNT + 1)]

    def get_selected_nodes(self):
        selected_nodes = []
        for n in range(1, self.SCRAPYD_SERVERS_AMOUNT + 1):
            if request.form.get(str(n)) == 'on':
                selected_nodes.append(n)
        return selected_nodes

    def get_response_from_view(self, url):
        # https://stackoverflow.com/a/21342070/10517783  How do I call one Flask view from another one?
        # https://stackoverflow.com/a/30250045/10517783
        # python - Flask test_client() doesn't have request.authorization with pytest
        client = app.test_client()
        if self.ENABLE_AUTH:
            headers = {'Authorization': _basic_auth_str(self.USERNAME, self.PASSWORD)}
        else:
            headers = {}
        response = client.get(url, headers=headers)
        return response.get_data(as_text=True)

    @staticmethod
    def get_now_string():
        return time.strftime('%Y-%m-%dT%H_%M_%S')

    @staticmethod
    def json_dumps(obj, sort_keys=True):
        return json_dumps(obj, sort_keys=sort_keys)

    def make_request(self, url, data=None, timeout=60, api=True, auth=None):
        """
        :param url: url to make request
        :param data: None or a dict object to post
        :param timeout: timeout when making request, in seconds
        :param api: return a dict object if set True, else text
        :param auth: None or (username, password) for basic auth
        """
        try:
            if 'addversion.json' in url and data:
                self.logger.debug('>>>>> POST %s' % url)
                self.logger.debug(json_dumps(dict(project=data['project'], version=data['version'],
                                                  egg="%s bytes binary egg file" % len(data['egg']))))
            else:
                self.logger.debug('>>>>> %s %s' % ('POST' if data else 'GET', url))
                if data:
                    self.logger.debug(json_dumps(data))

            if data:
                r = session.post(url, data=data, timeout=timeout, auth=auth)
            else:
                r = session.get(url, timeout=timeout, auth=auth)
            r.encoding = 'utf8'
        except Exception as err:
            self.logger.error('!!!!! %s %s' % (err.__class__.__name__, err))
            if api:
                r_json = dict(url=url, auth=auth, status_code=-1,
                              status='error', message=str(err), when=time.ctime())
                return -1, r_json
            else:
                return -1, str(err)
        else:
            if api:
                r_json = {}
                try:
                    r_json = r.json()
                except json.JSONDecodeError:  # listprojects would get 502 html when Scrapyd server reboots
                    r_json = {'status': 'error', 'message': r.text}
                finally:
                    # Scrapyd in PY2: Traceback (most recent call last):\\n
                    # Scrapyd in PY3: Traceback (most recent call last):\r\n
                    message = r_json.get('message', '')
                    if message:
                        r_json['message'] = re.sub(r'\\n', '\n', message)
                    r_json.update(dict(url=url, auth=auth, status_code=r.status_code, when=time.ctime()))
                    if r.status_code != 200 or r_json.get('status', '') != 'ok':
                        self.logger.error('!!!!! %s %s' % (r.status_code, url))
                        self.logger.error(json_dumps(r_json))
                    elif not url.endswith('daemonstatus.json'):
                        self.logger.debug('<<<<< %s %s' % (r.status_code, url))
                        self.logger.debug(json_dumps(r_json))

                    return r.status_code, r_json
            else:
                if r.status_code == 200:
                    front = r.text[:min(100, len(r.text))].replace('\n', '')
                    back = r.text[-min(100, len(r.text)):].replace('\n', '')
                    self.logger.debug('<<<<< %s %s\n...%s' % (r.status_code, front, back))
                else:
                    self.logger.error('!!!!! %s %s' % (r.status_code, r.text))

                return r.status_code, r.text
