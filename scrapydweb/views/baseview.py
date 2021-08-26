# coding: utf-8
import logging
import os
import re

from flask import current_app as app
from flask import Response, flash, g, request, url_for
from flask.views import View
from logparser import __version__ as LOGPARSER_VERSION
from six import text_type

from ..__version__ import __version__ as SCRAPYDWEB_VERSION
from ..common import (get_now_string, get_response_from_view, handle_metadata,
                      handle_slash, json_dumps, session)
from ..vars import (ALLOWED_SCRAPYD_LOG_EXTENSIONS, APSCHEDULER_DATABASE_URI,
                    DATA_PATH, DEMO_PROJECTS_PATH, DEPLOY_PATH, PARSE_PATH,
                    ALERT_TRIGGER_KEYS, LEGAL_NAME_PATTERN, SCHEDULE_ADDITIONAL,
                    SCHEDULE_PATH, STATE_PAUSED, STATE_RUNNING, STATS_PATH, STRICT_NAME_PATTERN)
from ..utils.scheduler import scheduler


class BaseView(View):
    SCRAPYDWEB_VERSION = SCRAPYDWEB_VERSION
    LOGPARSER_VERSION = LOGPARSER_VERSION

    DEMO_PROJECTS_PATH = DEMO_PROJECTS_PATH
    DEPLOY_PATH = DEPLOY_PATH
    PARSE_PATH = PARSE_PATH
    SCHEDULE_PATH = SCHEDULE_PATH
    STATS_PATH = STATS_PATH

    OK = 'ok'
    ERROR = 'error'
    NA = 'N/A'
    INFO = 'info'
    WARN = 'warning'
    DEFAULT_LATEST_VERSION = 'default: the latest version'
    LEGAL_NAME_PATTERN = LEGAL_NAME_PATTERN
    STRICT_NAME_PATTERN = STRICT_NAME_PATTERN
    ALERT_TRIGGER_KEYS = ALERT_TRIGGER_KEYS

    methods = ['GET', 'POST']

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Not in the config file
        self.DEFAULT_SETTINGS_PY_PATH = app.config['DEFAULT_SETTINGS_PY_PATH']
        self.SCRAPYDWEB_SETTINGS_PY_PATH = app.config['SCRAPYDWEB_SETTINGS_PY_PATH']
        self.MAIN_PID = app.config['MAIN_PID']
        self.LOGPARSER_PID = app.config['LOGPARSER_PID']
        self.POLL_PID = app.config['POLL_PID']

        # System
        self.DEBUG = app.config.get('DEBUG', False)
        self.VERBOSE = app.config.get('VERBOSE', False)
        self.DATA_PATH = DATA_PATH
        self.APSCHEDULER_DATABASE_URI = APSCHEDULER_DATABASE_URI
        self.SQLALCHEMY_DATABASE_URI = app.config['SQLALCHEMY_DATABASE_URI']
        self.SQLALCHEMY_BINDS = app.config['SQLALCHEMY_BINDS']

        _level = logging.DEBUG if self.VERBOSE else logging.INFO
        self.logger.setLevel(_level)
        logging.getLogger("requests").setLevel(_level)
        logging.getLogger("urllib3").setLevel(_level)

        # if app.testing:
        self.logger.debug('view_args of %s\n%s', request.url, self.json_dumps(request.view_args))
        if request.args:
            self.logger.debug('request.args of %s\n%s', request.url, self.json_dumps(request.args))
        if request.form:
            self.logger.debug('request.form from %s\n%s', request.url, self.json_dumps(request.form))
        if request.json:
            self.logger.debug('request.json from %s\n%s', request.url, self.json_dumps(request.json))
        if request.files:
            self.logger.debug('request.files from %s\n\n    %s\n', request.url, request.files)

        # ScrapydWeb
        self.SCRAPYDWEB_BIND = app.config.get('SCRAPYDWEB_BIND', '0.0.0.0')
        self.SCRAPYDWEB_PORT = app.config.get('SCRAPYDWEB_PORT', 5000)

        self.ENABLE_AUTH = app.config.get('ENABLE_AUTH', False)
        self.USERNAME = app.config.get('USERNAME', '')
        self.PASSWORD = app.config.get('PASSWORD', '')

        self.ENABLE_HTTPS = app.config.get('ENABLE_HTTPS', False)
        self.CERTIFICATE_FILEPATH = app.config.get('CERTIFICATE_FILEPATH', '')
        self.PRIVATEKEY_FILEPATH = app.config.get('PRIVATEKEY_FILEPATH', '')

        self.URL_SCRAPYDWEB = app.config.get('URL_SCRAPYDWEB', 'http://127.0.0.1:5000')

        # Scrapy
        self.SCRAPY_PROJECTS_DIR = app.config.get('SCRAPY_PROJECTS_DIR', '') or self.DEMO_PROJECTS_PATH

        # Scrapyd
        self.SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800']
        self.SCRAPYD_SERVERS_AMOUNT = len(self.SCRAPYD_SERVERS)
        self.SCRAPYD_SERVERS_GROUPS = app.config.get('SCRAPYD_SERVERS_GROUPS', []) or ['']
        self.SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', []) or [None]
        self.SCRAPYD_SERVERS_PUBLIC_URLS = (app.config.get('SCRAPYD_SERVERS_PUBLIC_URLS', None)
                                            or [''] * self.SCRAPYD_SERVERS_AMOUNT)

        self.LOCAL_SCRAPYD_SERVER = app.config.get('LOCAL_SCRAPYD_SERVER', '')
        self.LOCAL_SCRAPYD_LOGS_DIR = app.config.get('LOCAL_SCRAPYD_LOGS_DIR', '')
        self.SCRAPYD_LOG_EXTENSIONS = (app.config.get('SCRAPYD_LOG_EXTENSIONS', [])
                                       or ALLOWED_SCRAPYD_LOG_EXTENSIONS)

        # LogParser
        self.ENABLE_LOGPARSER = app.config.get('ENABLE_LOGPARSER', False)
        self.BACKUP_STATS_JSON_FILE = app.config.get('BACKUP_STATS_JSON_FILE', True)

        # Timer Tasks
        self.scheduler = scheduler
        self.JOBS_SNAPSHOT_INTERVAL = app.config.get('JOBS_SNAPSHOT_INTERVAL', 300)

        # Run Spider
        self.SCHEDULE_EXPAND_SETTINGS_ARGUMENTS = app.config.get('SCHEDULE_EXPAND_SETTINGS_ARGUMENTS', False)
        self.SCHEDULE_CUSTOM_USER_AGENT = app.config.get('SCHEDULE_CUSTOM_USER_AGENT', 'Mozilla/5.0')
        self.SCHEDULE_USER_AGENT = app.config.get('SCHEDULE_USER_AGENT', None)
        self.SCHEDULE_ROBOTSTXT_OBEY = app.config.get('SCHEDULE_ROBOTSTXT_OBEY', None)
        self.SCHEDULE_COOKIES_ENABLED = app.config.get('SCHEDULE_COOKIES_ENABLED', None)
        self.SCHEDULE_CONCURRENT_REQUESTS = app.config.get('SCHEDULE_CONCURRENT_REQUESTS', None)
        self.SCHEDULE_DOWNLOAD_DELAY = app.config.get('SCHEDULE_DOWNLOAD_DELAY', None)
        self.SCHEDULE_ADDITIONAL = app.config.get('SCHEDULE_ADDITIONAL', SCHEDULE_ADDITIONAL)

        # Page Display
        self.SHOW_SCRAPYD_ITEMS = app.config.get('SHOW_SCRAPYD_ITEMS', True)
        self.SHOW_JOBS_JOB_COLUMN = app.config.get('SHOW_JOBS_JOB_COLUMN', False)
        self.JOBS_FINISHED_JOBS_LIMIT = app.config.get('JOBS_FINISHED_JOBS_LIMIT', 0)
        self.JOBS_RELOAD_INTERVAL = app.config.get('JOBS_RELOAD_INTERVAL', 300)
        self.DAEMONSTATUS_REFRESH_INTERVAL = app.config.get('DAEMONSTATUS_REFRESH_INTERVAL', 10)

        # Send text
        self.SLACK_TOKEN = app.config.get('SLACK_TOKEN', '')
        self.SLACK_CHANNEL = app.config.get('SLACK_CHANNEL', '') or 'general'
        self.TELEGRAM_TOKEN = app.config.get('TELEGRAM_TOKEN', '')
        self.TELEGRAM_CHAT_ID = app.config.get('TELEGRAM_CHAT_ID', 0)
        self.EMAIL_SUBJECT = app.config.get('EMAIL_SUBJECT', '') or 'Email from #scrapydweb'

        # Monitor & Alert
        self.ENABLE_MONITOR = app.config.get('ENABLE_MONITOR', False)
        self.ENABLE_SLACK_ALERT = app.config.get('ENABLE_SLACK_ALERT', False)
        self.ENABLE_TELEGRAM_ALERT = app.config.get('ENABLE_TELEGRAM_ALERT', False)
        self.ENABLE_EMAIL_ALERT = app.config.get('ENABLE_EMAIL_ALERT', False)

        self.EMAIL_SENDER = app.config.get('EMAIL_SENDER', '')
        self.EMAIL_RECIPIENTS = app.config.get('EMAIL_RECIPIENTS', [])
        self.EMAIL_USERNAME = app.config.get('EMAIL_USERNAME', '') or self.EMAIL_SENDER
        self.EMAIL_PASSWORD = app.config.get('EMAIL_PASSWORD', '')

        self.SMTP_SERVER = app.config.get('SMTP_SERVER', '')
        self.SMTP_PORT = app.config.get('SMTP_PORT', 0)
        self.SMTP_OVER_SSL = app.config.get('SMTP_OVER_SSL', False)
        self.SMTP_CONNECTION_TIMEOUT = app.config.get('SMTP_CONNECTION_TIMEOUT', 30)

        self.EMAIL_KWARGS = dict(
            email_username=self.EMAIL_USERNAME,
            email_password=self.EMAIL_PASSWORD,
            email_sender=self.EMAIL_SENDER,
            email_recipients=self.EMAIL_RECIPIENTS,
            smtp_server=self.SMTP_SERVER,
            smtp_port=self.SMTP_PORT,
            smtp_over_ssl=self.SMTP_OVER_SSL,
            smtp_connection_timeout=self.SMTP_CONNECTION_TIMEOUT,
            subject='subject',
            content='content'
        )

        self.POLL_ROUND_INTERVAL = app.config.get('POLL_ROUND_INTERVAL', 300)
        self.POLL_REQUEST_INTERVAL = app.config.get('POLL_REQUEST_INTERVAL', 10)
        self.ALERT_WORKING_DAYS = app.config.get('ALERT_WORKING_DAYS', [])
        self.ALERT_WORKING_HOURS = app.config.get('ALERT_WORKING_HOURS', [])
        self.ON_JOB_RUNNING_INTERVAL = app.config.get('ON_JOB_RUNNING_INTERVAL', 0)
        self.ON_JOB_FINISHED = app.config.get('ON_JOB_FINISHED', False)
        # ['CRITICAL', 'ERROR', 'WARNING', 'REDIRECT', 'RETRY', 'IGNORE']
        for key in self.ALERT_TRIGGER_KEYS:
            setattr(self, 'LOG_%s_THRESHOLD' % key, app.config.get('LOG_%s_THRESHOLD' % key, 0))
            setattr(self, 'LOG_%s_TRIGGER_STOP' % key, app.config.get('LOG_%s_TRIGGER_STOP' % key, False))
            setattr(self, 'LOG_%s_TRIGGER_FORCESTOP' % key, app.config.get('LOG_%s_TRIGGER_FORCESTOP' % key, False))

        # Other attributes not from config
        self.view_args = request.view_args
        self.node = self.view_args['node']
        assert 0 < self.node <= self.SCRAPYD_SERVERS_AMOUNT, \
            'node index error: %s, which should be between 1 and %s' % (self.node, self.SCRAPYD_SERVERS_AMOUNT)
        self.SCRAPYD_SERVER = self.SCRAPYD_SERVERS[self.node - 1]
        self.IS_LOCAL_SCRAPYD_SERVER = self.SCRAPYD_SERVER == self.LOCAL_SCRAPYD_SERVER
        self.GROUP = self.SCRAPYD_SERVERS_GROUPS[self.node - 1]
        self.AUTH = self.SCRAPYD_SERVERS_AUTHS[self.node - 1]
        self.SCRAPYD_SERVER_PUBLIC_URL = self.SCRAPYD_SERVERS_PUBLIC_URLS[self.node - 1]

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

        self.USE_MOBILEUI = request.args.get('ui', '') == 'mobile'
        self.UI = 'mobile' if self.USE_MOBILEUI else None
        self.GET = request.method == 'GET'
        self.POST = request.method == 'POST'

        self.FEATURES = ''
        self.FEATURES += 'A' if self.ENABLE_AUTH else '-'
        self.FEATURES += 'D' if handle_metadata().get('jobs_style') == 'database' else 'C'
        self.FEATURES += 'd' if self.SCRAPY_PROJECTS_DIR != self.DEMO_PROJECTS_PATH else '-'
        self.FEATURES += 'L' if self.ENABLE_LOGPARSER else '-'
        self.FEATURES += 'Sl' if self.ENABLE_SLACK_ALERT else '-'
        self.FEATURES += 'Tg' if self.ENABLE_TELEGRAM_ALERT else '-'
        self.FEATURES += 'Em' if self.ENABLE_EMAIL_ALERT else '-'
        self.FEATURES += 'P' if self.IS_MOBILE else '-'
        self.FEATURES += 'M' if self.USE_MOBILEUI else '-'
        self.FEATURES += 'S' if self.ENABLE_HTTPS else '-'
        self.any_running_apscheduler_jobs = any(job.next_run_time
                                                for job in self.scheduler.get_jobs(jobstore='default'))
        if self.scheduler.state == STATE_PAUSED:
            self.FEATURES += '-'
        elif self.any_running_apscheduler_jobs:
            self.FEATURES += 'T'
        else:
            self.FEATURES += 't'
        if not self.SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
            self.FEATURES += self.SQLALCHEMY_DATABASE_URI[:3]

        self.template_fail = 'scrapydweb/fail_mobileui.html' if self.USE_MOBILEUI else 'scrapydweb/fail.html'
        self.update_g()

    @staticmethod
    def get_job_without_ext(job):
        if job.endswith('.tar.gz'):
            return job[:-len('.tar.gz')]
        else:
            return os.path.splitext(job)[0]  # '1.1.log' => ('1.1', '.log')

    @staticmethod
    def get_now_string(allow_space=False):
        return get_now_string(allow_space=allow_space)

    def get_response_from_view(self, url, data=None, as_json=False):
        auth = (self.USERNAME, self.PASSWORD) if self.ENABLE_AUTH else None
        return get_response_from_view(url, auth=auth, data=data, as_json=as_json)

    def get_selected_nodes(self):
        selected_nodes = []
        for n in range(1, self.SCRAPYD_SERVERS_AMOUNT + 1):
            if request.form.get(str(n)) == 'on':
                selected_nodes.append(n)
        return selected_nodes

    @staticmethod
    def handle_slash(string):
        return handle_slash(string)

    @staticmethod
    def json_dumps(obj, sort_keys=True, indent=4, ensure_ascii=False, as_response=False):
        # flask.jsonify
        # https://flask.palletsprojects.com/en/1.1.x/config/#JSONIFY_MIMETYPE
        # https://stackoverflow.com/questions/11773348/python-flask-how-to-set-content-type
        # https://stackoverflow.com/questions/9254891/what-does-content-type-application-json-charset-utf-8-really-mean
        js = json_dumps(obj, sort_keys=sort_keys, indent=indent, ensure_ascii=ensure_ascii)
        if as_response:
            # Content-Type: application/json
            return Response(js, mimetype='application/json')
        else:
            return js

    @staticmethod
    def remove_microsecond(dt):
        return str(dt)[:19]

    def make_request(self, url, data=None, auth=None, as_json=True, dumps_json=True, check_status=True, timeout=60):
        """
        :param url: url to make request
        :param data: None or a dict object to post
        :param auth: None or (username, password) for basic auth
        :param as_json: return a dict object if set True, else text
        :param dumps_json: whether to dumps the json response when as_json is set to True
        :param check_status: whether to log error when status != 'ok'
        :param timeout: timeout when making request, in seconds
        """
        try:
            if 'addversion.json' in url and data:
                self.logger.debug(">>>>> POST %s", url)
                self.logger.debug(self.json_dumps(dict(project=data['project'], version=data['version'],
                                                  egg="%s bytes binary egg file" % len(data['egg']))))
            else:
                self.logger.debug(">>>>> %s %s", 'POST' if data else 'GET', url)
                if data:
                    self.logger.debug("POST data: %s", self.json_dumps(data))

            if data:
                r = session.post(url, data=data, auth=auth, timeout=timeout)
            else:
                r = session.get(url, auth=auth, timeout=timeout)
            r.encoding = 'utf-8'
        except Exception as err:
            # self.logger.error('!!!!! %s %s' % (err.__class__.__name__, err))
            self.logger.error("!!!!! error with %s: %s", url, err)
            if as_json:
                r_json = dict(url=url, auth=auth, status_code=-1, status=self.ERROR,
                              message=str(err), when=self.get_now_string(True))
                return -1, r_json
            else:
                return -1, str(err)
        else:
            if as_json:
                r_json = {}
                try:
                    # listprojects would get 502 html when Scrapyd server reboots
                    r_json = r.json()  # PY3: json.decoder.JSONDecodeError  PY2: exceptions.ValueError
                except ValueError as err:  # issubclass(JSONDecodeError, ValueError)
                    self.logger.error("Fail to decode json from %s: %s", url, err)
                    r_json = dict(status=self.ERROR, message=r.text)
                finally:
                    # Scrapyd in Python2: Traceback (most recent call last):\\n
                    # Scrapyd in Python3: Traceback (most recent call last):\r\n
                    message = r_json.get('message', '')
                    if message and not isinstance(message, dict):
                        r_json['message'] = re.sub(r'\\n', '\n', message)
                    r_json.update(dict(url=url, auth=auth, status_code=r.status_code, when=self.get_now_string(True)))
                    status = r_json.setdefault('status', self.NA)
                    if r.status_code != 200 or (check_status and status != self.OK):
                        self.logger.error("!!!!! (%s) %s: %s", r.status_code, status, url)
                    else:
                        self.logger.debug("<<<<< (%s) %s: %s", r.status_code, status, url)
                    if dumps_json:
                        self.logger.debug("Got json from %s: %s", url, self.json_dumps(r_json))
                    else:
                        self.logger.debug("Got keys from (%s) %s %s: %s",
                                          r_json.get('status_code'), r_json.get('status'), url, r_json.keys())

                    return r.status_code, r_json
            else:
                if r.status_code == 200:
                    _text = r.text[:100] + '......' + r.text[-100:] if len(r.text) > 200 else r.text
                    self.logger.debug("<<<<< (%s) %s\n%s", r.status_code, url, repr(_text))
                else:
                    self.logger.error("!!!!! (%s) %s\n%s", r.status_code, url, r.text)

                return r.status_code, r.text

    def update_g(self):
        # g lifetime: every single request
        # Note that use inject_variable() in View class would cause memory leak, issue #14
        g.IS_MOBILE = self.IS_MOBILE
        g.url_jobs_list = [url_for('jobs', node=node, ui=self.UI)
                           for node in range(1, self.SCRAPYD_SERVERS_AMOUNT + 1)]
        g.multinode = ('<label title="multinode">'
                       '<svg class="icon" aria-hidden="true"><use xlink:href="#icon-servers"></use></svg>'
                       '</label>')
        # For base.html
        if not self.USE_MOBILEUI:
            g.url_daemonstatus = url_for('api', node=self.node, opt='daemonstatus')
            g.url_menu_servers = url_for('servers', node=self.node)
            g.url_menu_jobs = url_for('jobs', node=self.node)
            g.url_menu_nodereports = url_for('nodereports', node=self.node)
            g.url_menu_clusterreports = url_for('clusterreports', node=self.node)
            g.url_menu_tasks = url_for('tasks', node=self.node)
            g.url_menu_deploy = url_for('deploy', node=self.node)
            g.url_menu_schedule = url_for('schedule', node=self.node)
            g.url_menu_projects = url_for('projects', node=self.node)
            g.url_menu_logs = url_for('logs', node=self.node)
            g.url_menu_items = url_for('items', node=self.node)
            g.url_menu_sendtext = url_for('sendtext', node=self.node)
            g.url_menu_parse = url_for('parse.upload', node=self.node)
            g.url_menu_settings = url_for('settings', node=self.node)
            g.url_menu_mobileui = url_for('index', node=self.node, ui='mobile')
            g.scheduler_state_paused = self.scheduler.state == STATE_PAUSED and self.any_running_apscheduler_jobs
            g.scheduler_state_running = self.scheduler.state == STATE_RUNNING and self.any_running_apscheduler_jobs

    # Issue#48 [PY2] UnicodeDecodeError raised when there are some files with illegal filenames in `SCRAPY_PROJECTS_DIR`
    # https://stackoverflow.com/questions/21772271/unicodedecodeerror-when-performing-os-walk
    # https://xuanwo.io/2018/04/01/python-os-walk/
    # Tested in Ubuntu:
    # touch $(echo -e "\x8b\x8bFile")
    # mkdir $(echo -e "\x8b\x8bFolder")
    def safe_walk(self, top, topdown=True, onerror=None, followlinks=False):
        islink, join, isdir = os.path.islink, os.path.join, os.path.isdir

        # touch $(echo -e "\x8b\x8bThis is a bad filename")
        # ('top: ', u'/home/username/download/scrapydweb/scrapydweb/data/demo_projects/ScrapydWeb_demo')
        # ('names: ', ['\x8b\x8bThis', u'ScrapydWeb_demo', u'filename', u'scrapy.cfg', u'a', u'is', u'bad'])
        try:
            names = os.listdir(top)
        except OSError as err:
            if onerror is not None:
                onerror(err)
            return

        new_names = []
        for name in names:
            if isinstance(name, text_type):
                new_names.append(name)
            else:
                msg = "Ignore non-unicode filename %s in %s" % (repr(name), top)
                self.logger.error(msg)
                flash(msg, self.WARN)
        names = new_names

        dirs, nondirs = [], []
        for name in names:
            if isdir(join(top, name)):
                dirs.append(name)
            else:
                nondirs.append(name)

        if topdown:
            yield top, dirs, nondirs
        for name in dirs:
            new_path = join(top, name)
            if followlinks or not islink(new_path):
                for x in self.safe_walk(new_path, topdown, onerror, followlinks):
                    yield x
        if not topdown:
            yield top, dirs, nondirs


class MetadataView(BaseView):

    def __init__(self):
        super(MetadataView, self).__init__()

    def dispatch_request(self, **kwargs):
        return self.json_dumps(handle_metadata(), as_response=True)
