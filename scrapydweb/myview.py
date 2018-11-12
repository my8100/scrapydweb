# coding: utf8
import time
import json
import logging

import requests
from requests.auth import _basic_auth_str
from flask import request
from flask import current_app as app
from flask.views import View

from .vars import DEMO_PROJECTS_PATH, ALLOWED_SCRAPYD_LOG_EXTENSIONS, EMAIL_TRIGGER_KEYS
from .utils.utils import json_dumps


session = requests.Session()
session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=1000, pool_maxsize=1000))
session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=1000, pool_maxsize=1000))


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

        if request.form:
            self.logger.debug(self.json_dumps(request.form))

        # ScrapydWeb
        self.SCRAPYDWEB_BIND = app.config.get('SCRAPYDWEB_BIND', '0.0.0.0')
        self.SCRAPYDWEB_PORT = app.config.get('SCRAPYDWEB_PORT', 5000)

        self.DISABLE_AUTH = app.config.get('DISABLE_AUTH', True)
        self.USERNAME = app.config.get('USERNAME', '')
        self.PASSWORD = app.config.get('PASSWORD', '')

        # Scrapy
        self.SCRAPY_PROJECTS_DIR = app.config.get('SCRAPY_PROJECTS_DIR', '') or DEMO_PROJECTS_PATH

        # Scrapyd
        self.SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800']
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
        self.DISABLE_CACHE = app.config.get('DISABLE_CACHE', False)
        self.CACHE_ROUND_INTERVAL = app.config.get('CACHE_ROUND_INTERVAL', 300)
        self.CACHE_REQUEST_INTERVAL = app.config.get('CACHE_REQUEST_INTERVAL', 10)
        self.DELETE_CACHE = app.config.get('DELETE_CACHE', False)

        # Email Notice
        self.DISABLE_EMAIL = app.config.get('DISABLE_EMAIL', True)
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
        self.SCRAPYD_SERVER = self.SCRAPYD_SERVERS[self.node - 1]
        self.GROUP = self.SCRAPYD_SERVERS_GROUPS[self.node - 1]
        self.AUTH = self.SCRAPYD_SERVERS_AUTHS[self.node - 1]

        self.IS_SIMPLEUI = True if request.args.get('ui', '') == 'simple' else False
        self.UI = 'simple' if self.IS_SIMPLEUI else None
        self.GET = True if request.method == 'GET' else False
        self.POST = True if request.method == 'POST' else False

        self.AUTH_ENABLED = not self.DISABLE_AUTH
        self.CACHE_ENABLED = not self.DISABLE_CACHE
        self.EMAIL_ENABLED = not self.DISABLE_EMAIL

        self.template_result = 'scrapydweb/simpleui/result.html' if self.IS_SIMPLEUI else 'scrapydweb/result.html'

    def get_selected_nodes(self):
        selected_nodes = []
        for i in range(1, len(self.SCRAPYD_SERVERS) + 1):
            if request.form.get(str(i)) == 'on':
                selected_nodes.append(i)
        return selected_nodes

    def get_response_from_view(self, url):
        # https://stackoverflow.com/a/21342070/10517783  How do I call one Flask view from another one?
        # https://stackoverflow.com/a/30250045/10517783
        # python - Flask test_client() doesn't have request.authorization with pytest
        client = app.test_client()
        if self.AUTH_ENABLED:
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
        :param api: return a dict object if set True, else text
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
                return -1, {'url': url, 'auth': auth, 'status_code': -1,
                            'status': 'error', 'message': str(err)}
            else:
                return -1, str(err)
        else:
            if api:
                try:
                    r_json = r.json()
                except json.JSONDecodeError:  # When Scrapyd server reboot, listprojects got 502 html
                    r_json = {'status': 'error', 'message': r.text}
                finally:
                    r_json.update(dict(url=url, auth=auth, status_code=r.status_code, when=time.ctime()))

                    sign = '!!!!! ' if (r.status_code != 200 or r_json.get('status') != 'ok') else '<<<<< '
                    self.logger.debug('%s%s %s' % (sign, r.status_code, url))
                    self.logger.debug(json_dumps(r_json))

                    return r.status_code, r_json
            else:
                if r.status_code == 200:
                    front = r.text[:min(100, len(r.text))].replace('\n', '')
                    back = r.text[-min(100, len(r.text)):].replace('\n', '')
                    self.logger.debug('<<<<< %s %s\n...%s' % (r.status_code, front, back))
                else:
                    self.logger.debug('!!!!! %s %s' % (r.status_code, r.text))

                return r.status_code, r.text
