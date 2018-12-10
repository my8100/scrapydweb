# coding: utf8
import os
import re
from collections import defaultdict, OrderedDict

from flask import render_template

from ..myview import MyView
from ..vars import EMAIL_TRIGGER_KEYS
from ..utils.utils import json_dumps


CWD = os.path.dirname(os.path.abspath(__file__))


class SettingsView(MyView):
    methods = ['GET']

    def __init__(self):
        super(self.__class__, self).__init__()

        self.template = 'scrapydweb/settings.html'
        self.kwargs = dict(node=self.node)

    def dispatch_request(self, **kwargs):
        self.update_kwargs()
        return render_template(self.template, **self.kwargs)

    @staticmethod
    def protect(string):
        if not isinstance(string, str):
            return string
        length = len(string)
        if length == 0:
            return string
        elif length < 3:
            return re.sub(r'^.', '*', string)
        elif length < 7:
            return re.sub(r'^.(.*?).$', r'*\1*', string)
        else:
            return re.sub(r'^..(.*?)..$', r'**\1**', string)

    @staticmethod
    def json_dumps(obj, sort_keys=False):
        string = json_dumps(obj, sort_keys=sort_keys)
        return string.replace(' true', ' True').replace(' false', ' False').replace(' null', ' None')

    def update_kwargs(self):
        # User settings
        self.kwargs['default_settings_py'] = os.path.join(os.path.dirname(CWD), 'default_settings.py')

        # ScrapydWeb
        self.kwargs['scrapydweb_server'] = self.json_dumps(dict(
            SCRAPYDWEB_BIND=self.SCRAPYDWEB_BIND,
            SCRAPYDWEB_PORT=self.SCRAPYDWEB_PORT,
            ENABLE_AUTH=self.ENABLE_AUTH,
            USERNAME=self.protect(self.USERNAME),
            PASSWORD=self.protect(self.PASSWORD)
        ))

        # Scrapy
        self.kwargs['SCRAPY_PROJECTS_DIR'] = self.SCRAPY_PROJECTS_DIR or "''"

        # Scrapyd
        servers = defaultdict(list)
        for group, server, auth in zip(self.SCRAPYD_SERVERS_GROUPS, self.SCRAPYD_SERVERS, self.SCRAPYD_SERVERS_AUTHS):
            _server = '%s:%s@%s' % (self.protect(auth[0]), self.protect(auth[1]), server) if auth else server
            servers[group].append(_server)

        self.kwargs['servers'] = self.json_dumps(servers)
        self.kwargs['SCRAPYD_LOGS_DIR'] = self.SCRAPYD_LOGS_DIR or "''"
        self.kwargs['SCRAPYD_LOG_EXTENSIONS'] = self.SCRAPYD_LOG_EXTENSIONS

        # Page Display
        self.kwargs['page_display_details'] = self.json_dumps(dict(
            SHOW_SCRAPYD_ITEMS=self.SHOW_SCRAPYD_ITEMS,
            SHOW_DASHBOARD_JOB_COLUMN=self.SHOW_DASHBOARD_JOB_COLUMN,
            DASHBOARD_RELOAD_INTERVAL=self.DASHBOARD_RELOAD_INTERVAL,
            DAEMONSTATUS_REFRESH_INTERVAL=self.DAEMONSTATUS_REFRESH_INTERVAL
        ))

        # HTML Caching
        self.kwargs['ENABLE_CACHE'] = self.ENABLE_CACHE
        self.kwargs['html_caching_details'] = self.json_dumps(dict(
            CACHE_ROUND_INTERVAL=self.CACHE_ROUND_INTERVAL,
            CACHE_REQUEST_INTERVAL=self.CACHE_REQUEST_INTERVAL,
            DELETE_CACHE=self.DELETE_CACHE
        ))

        # Email Notice
        self.kwargs['ENABLE_EMAIL'] = self.ENABLE_EMAIL
        self.kwargs['smtp_settings'] = self.json_dumps(dict(
            SMTP_SERVER=self.SMTP_SERVER,
            SMTP_PORT=self.SMTP_PORT,
            SMTP_OVER_SSL=self.SMTP_OVER_SSL,
            SMTP_CONNECTION_TIMEOUT=self.SMTP_CONNECTION_TIMEOUT
        ))

        self.kwargs['sender_recipients'] = self.json_dumps(dict(
            FROM_ADDR=self.FROM_ADDR,
            EMAIL_PASSWORD=self.protect(self.EMAIL_PASSWORD),
            TO_ADDRS=self.TO_ADDRS
        ))

        self.kwargs['email_working_time'] = self.json_dumps([
            dict(
                EMAIL_WORKING_DAYS="%s" % sorted(self.EMAIL_WORKING_DAYS),  # stringify making it displayed in a line
                remark="Monday is 1 and Sunday is 7"
            ),
            dict(
                EMAIL_WORKING_HOURS="%s" % sorted(self.EMAIL_WORKING_HOURS),
                remark="From 0 to 23"
            )
        ])

        # email triggers
        d = OrderedDict()
        d['ON_JOB_RUNNING_INTERVAL'] = self.ON_JOB_RUNNING_INTERVAL
        d['ON_JOB_FINISHED'] = self.ON_JOB_FINISHED

        for key in EMAIL_TRIGGER_KEYS:
            keys = ['LOG_%s_THRESHOLD' % key, 'LOG_%s_TRIGGER_STOP' % key, 'LOG_%s_TRIGGER_FORCESTOP' % key]
            d[key] = {k: getattr(self, k) for k in keys}
        value = self.json_dumps(d)
        value = re.sub(r'True', "<b style='color: red'>True</b>", value)
        value = re.sub(r'(\s[1-9]\d*)', r"<b style='color: red'>\1</b>", value)
        self.kwargs['email_triggers'] = value

        # System
        self.kwargs['DEBUG'] = self.DEBUG
        self.kwargs['VERBOSE'] = self.VERBOSE
