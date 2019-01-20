# coding: utf8
from collections import OrderedDict
from datetime import date, datetime
import io
import json
import os
from subprocess import Popen
import sys
import tarfile
import time

from flask import flash, render_template, request, url_for
from logparser import parse

from ..myview import MyView


CWD = os.path.dirname(os.path.abspath(__file__))
EMAIL_CONTENT_KEYS = [
    'log_critical_count',
    'log_error_count',
    'log_warning_count',
    'log_redirect_count',
    'log_retry_count',
    'log_ignore_count',
    'crawled_pages',
    'scraped_items'
]
job_data_dict = {}
# job_finished_set would only be updated by poll POST with ?job_finished=True > email_notice(),
# used for determining whether to show 'click to refresh' button in the Log and Stats page.
job_finished_set = set()


# http://flask.pocoo.org/docs/1.0/api/#flask.views.View
# http://flask.pocoo.org/docs/1.0/views/
class LogView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()  # super().__init__()

        self.opt = self.view_args['opt']
        self.project = self.view_args['project']
        self.spider = self.view_args['spider']
        self.job = self.view_args['job']

        self.job_key = '/%s/%s/%s/%s' % (self.node, self.project, self.spider, self.job)
        self.job_data_dict = job_data_dict
        self.job_finished_set = job_finished_set

        self.local_scrapyd_server = self.SCRAPYD_SERVER.split(':')[0] in ['127.0.0.1', 'localhost']

        # Note that self.SCRAPYD_LOGS_DIR may be an empty string
        # Extension like '.log' is excluded here.
        self.url = u'http://{}/logs/{}/{}/{}'.format(self.SCRAPYD_SERVER, self.project, self.spider, self.job)
        self.log_path = os.path.join(self.SCRAPYD_LOGS_DIR, self.project, self.spider, self.job)

        # For Log and Stats buttons in the Logs page: /a.log/?with_ext=True
        self.with_ext = request.args.get('with_ext', None)
        if self.with_ext:
            self.SCRAPYD_LOG_EXTENSIONS = ['']

        # 'a', 'a.log', 'a.tar.gz' => 'a'
        job_without_ext = self.job.split('.')[0]
        # json file by LogParser
        self.json_path = os.path.join(self.SCRAPYD_LOGS_DIR, self.project, self.spider, job_without_ext + '.json')
        self.json_url = u'http://{}/logs/{}/{}/{}.json'.format(self.SCRAPYD_SERVER, self.project, self.spider,
                                                               job_without_ext)

        self.status_code = 0
        self.text = ''
        self.template = 'scrapydweb/%s%s.html' % (self.opt, '_mobileui' if self.USE_MOBILEUI else '')
        self.kwargs = dict(node=self.node, project=self.project, spider=self.spider,
                           job=job_without_ext if self.with_ext else self.job,
                           url_refresh='', url_jump='')

        # Request that comes from poll POST for finished job and links of finished job in the Dashboard page
        # would be attached with the query string '?job_finished=True'
        self.job_finished = request.args.get('job_finished', None)

        if self.opt == 'utf8':
            flash("It's recommended to check out the latest log via: the Stats page >> View log >> Tail", self.WARN)
            self.utf8_realtime = True
            self.stats_realtime = False
            self.stats_logparser = False
        else:
            self.utf8_realtime = False
            self.stats_realtime = True if request.args.get('realtime', None) else False
            self.stats_logparser = not self.stats_realtime
        self.logparser_valid = False

        # job_data for email notice: ([0] * 8, [False] * 6, False, time.time())
        self.job_stats_previous = []
        self.triggered_list = []
        self.has_been_stopped = False
        self.last_send_timestamp = 0
        self.job_stats = []
        self.job_stats_diff = []
        self.email_content_kwargs = {}
        self.flag = ''

    def dispatch_request(self, **kwargs):
        # Try to request stats by LogParser to avoid reading/requesting the entire raw log
        if self.stats_logparser:
            if self.local_scrapyd_server and self.SCRAPYD_LOGS_DIR:
                self.kwargs.update(self.read_local_stats_by_logparser())
            if not self.logparser_valid:
                self.kwargs.update(self.request_stats_by_logparser())

        if not self.logparser_valid and not self.text:
            # Try to read local logfile
            if self.local_scrapyd_server and self.SCRAPYD_LOGS_DIR:
                self.read_local_scrapy_log()
            # Has to request scrapy log
            if not self.text:
                self.request_scrapy_log()
                if self.status_code != 200:
                    kwargs = dict(
                        node=self.node,
                        url=self.url,
                        status_code=self.status_code,
                        text=self.text
                    )
                    return render_template(self.template_fail, **kwargs)

        self.update_kwargs()

        if self.ENABLE_EMAIL and self.POST:  # Only poll.py would make POST request
            self.email_notice()

        return render_template(self.template, **self.kwargs)

    def read_local_stats_by_logparser(self):
        self.logger.debug("Try to read local stats by LogParser: %s", self.json_path)
        js = {}
        if os.path.exists(self.json_path):
            try:
                with io.open(self.json_path, 'r', encoding='utf-8') as f:
                    js = json.loads(f.read())
                assert 'logparser_version' in js, "'logparser_version' NOT found in stats by LogParser: %s" % js
            except Exception as err:
                self.logger.error("Fail to read local stats by LogParser: %s", err)
            else:
                self.logparser_valid = True
                msg = "LogParser v%s, last_update_time: %s, %s" % (js['logparser_version'],
                                                                   js['last_update_time'], self.json_path)
                self.logger.info(msg)
                flash(msg, self.INFO)
        else:
            self.logger.warning("Fail to find local stats by LogParser: %s", self.json_path)
        return js

    def request_stats_by_logparser(self):
        self.logger.debug("Try to request stats by LogParser: %s", self.json_url)
        # self.make_request() would check the value of key 'status' if api=True
        status_code, js = self.make_request(self.json_url, auth=self.AUTH, api=True, json_dumps=False)
        if status_code != 200:
            self.logger.error("Fail to request stats by LogParser, got status_code: %s", status_code)
            flash("'pip install logparser' on the current Scrapyd host and "
                  "get it started via command 'logparser'", self.WARN)
        elif 'logparser_version' not in js:
            self.logger.warning("'logparser_version' NOT found in stats by LogParser: %s", js)
            flash("'logparser_version' NOT found in the stats by LogParser (%s)" % self.json_url, self.WARN)
        else:
            self.logparser_valid = True
            msg = "LogParser v%s, last_update_time: %s, %s" % (js['logparser_version'], js['last_update_time'],
                                                               self.json_url)
            self.logger.info(msg)
            flash(msg, self.INFO)
        return js

    def read_local_scrapy_log(self):
        for ext in self.SCRAPYD_LOG_EXTENSIONS:
            log_path = self.log_path + ext
            if os.path.exists(log_path):
                if tarfile.is_tarfile(log_path):
                    self.logger.debug("Ignore local tarfile and use requests instead: %s", log_path)
                    break
                with io.open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    self.text = f.read()
                self.logger.debug("Using local logfile: %s", log_path)
                flash("Using local logfile: %s" % log_path, self.INFO)
                break

    def request_scrapy_log(self):
        for ext in self.SCRAPYD_LOG_EXTENSIONS:
            url = self.url + ext
            self.status_code, self.text = self.make_request(url, auth=self.AUTH, api=False)
            if self.status_code == 200:
                self.url = url
                self.logger.debug("Got logfile from %s", self.url)
                break
        else:
            self.logger.warning("Fail to request logfile from %s with extensions %s",
                                self.url, self.SCRAPYD_LOG_EXTENSIONS)
            self.url = '%s%s' % (self.url, self.SCRAPYD_LOG_EXTENSIONS[0])

    def update_kwargs(self):
        if self.utf8_realtime:
            self.kwargs['text'] = self.text
            self.kwargs['last_update_timestamp'] = time.time()
            if self.job_finished or self.job_key in self.job_finished_set:
                self.kwargs['url_refresh'] = ''
            else:
                self.kwargs['url_refresh'] = 'javascript:location.reload(true);'
        else:
            # Parsed data comes from json.loads, for compatibility with Python 2, 
            # use str(time_) to avoid [u'2019-01-01 00:00:01', 0, 0, 0, 0] in JavaScript.
            if self.logparser_valid:
                for d in self.kwargs['datas']:
                    d[0] = str(d[0])
            else:
                self.logger.warning('Parse the entire raw log')
                self.kwargs.update(parse(self.text))

            if (self.kwargs['finish_reason'] == self.NA
               and not self.job_finished
               and self.job_key not in self.job_finished_set):
                # http://flask.pocoo.org/docs/1.0/api/#flask.Request.url_root
                # _query_string = '?ui=mobile'
                # self.url_refresh = request.script_root + request.path + _query_string
                self.kwargs['url_refresh'] = 'javascript:location.reload(true);'
            if self.kwargs['url_refresh']:
                if self.stats_logparser and not self.logparser_valid:
                    self.kwargs['url_jump'] = ''
                else:
                    self.kwargs['url_jump'] = url_for('log', node=self.node, opt='stats', project=self.project,
                                                      spider=self.spider, job=self.job, with_ext=self.with_ext,
                                                      ui=self.UI, realtime='True' if self.stats_logparser else None)

        # Stats link of 'a.json' from the Logs page should hide these links
        if self.with_ext and self.job.endswith('.json'):
            self.kwargs['url_source'] = ''
            self.kwargs['url_opt_opposite'] = ''
            self.kwargs['url_refresh'] = ''
            self.kwargs['url_jump'] = ''
        else:
            self.kwargs['url_source'] = self.url
            self.kwargs['url_opt_opposite'] = url_for('log', node=self.node,
                                                      opt='utf8' if self.opt == 'stats' else 'stats',
                                                      project=self.project, spider=self.spider, job=self.job,
                                                      job_finished=self.job_finished, with_ext=self.with_ext,
                                                      ui=self.UI)

    def email_notice(self):
        job_data_default = ([0] * 8, [False] * 6, False, time.time())
        job_data = self.job_data_dict.setdefault(self.job_key, job_data_default)
        (self.job_stats_previous, self.triggered_list, self.has_been_stopped, self.last_send_timestamp) = job_data
        self.logger.info(self.job_data_dict)
        self.job_stats = [self.kwargs['log_categories'][k.lower() + '_logs']['count']
                          for k in self.EMAIL_TRIGGER_KEYS]
        self.job_stats.extend([self.kwargs['pages'], self.kwargs['items']])
        self.job_stats_diff = [j - i for i, j in zip(self.job_stats_previous, self.job_stats)]

        self.set_email_content_kwargs()
        self.set_email_flag()
        self.handle_email_flag()

    def set_email_content_kwargs(self):
        # For compatibility with Python 2, use OrderedDict() to keep insertion order
        self.email_content_kwargs = OrderedDict()
        self.email_content_kwargs['SCRAPYD_SERVER'] = self.SCRAPYD_SERVER
        self.email_content_kwargs['project'] = self.kwargs['project']
        self.email_content_kwargs['spider'] = self.kwargs['spider']
        self.email_content_kwargs['job'] = self.kwargs['job']
        self.email_content_kwargs['start_time'] = self.kwargs['first_log_time']
        self.email_content_kwargs['latest_log_time'] = self.kwargs['latest_log_time']
        self.email_content_kwargs['elapsed'] = self.kwargs['elapsed']
        self.email_content_kwargs['shutdown_reason'] = self.kwargs['shutdown_reason']
        self.email_content_kwargs['finish_reason'] = self.kwargs['finish_reason']
        self.email_content_kwargs['url_stats'] = request.url + '%sui=mobile' % '&' if request.args else '?'

        for idx, i in enumerate(EMAIL_CONTENT_KEYS):
            if self.job_stats_diff[idx]:
                self.email_content_kwargs[i] = '%s + %s' % (self.job_stats_previous[idx], self.job_stats_diff[idx])
            else:
                self.email_content_kwargs[i] = self.job_stats[idx]

        _bind = '127.0.0.1' if self.SCRAPYDWEB_BIND == '0.0.0.0' else self.SCRAPYDWEB_BIND
        _url_stop = url_for('api', node=self.node, opt='stop', project=self.project, version_spider_job=self.job)
        self.email_content_kwargs['url_stop'] = 'http://%s:%s%s' % (_bind, self.SCRAPYDWEB_PORT, _url_stop)

        now_timestamp = time.time()
        for k in ['latest_crawl', 'latest_scrape', 'latest_log']:
            ts = self.kwargs['%s_timestamp' % k]
            self.email_content_kwargs[k] = self.NA if ts == 0 else "%s seconds ago" % int(now_timestamp - ts)

        self.email_content_kwargs['current_time'] = self.get_now_string(True)
        self.email_content_kwargs['logparser_version'] = self.kwargs.get('logparser_version', self.NA)

    def set_email_flag(self):
        if self.ON_JOB_FINISHED and self.job_finished:
            self.flag = 'Finished'
        elif not all(self.triggered_list):
            to_forcestop = False
            to_stop = False
            # The order of the elements in EMAIL_TRIGGER_KEYS matters:
            # ['CRITICAL', 'ERROR', 'WARNING', 'REDIRECT', 'RETRY', 'IGNORE']
            for idx, key in enumerate(self.EMAIL_TRIGGER_KEYS):
                if (0 < getattr(self, 'LOG_%s_THRESHOLD' % key, 0) <= self.job_stats[idx]
                   and not self.triggered_list[idx]):
                    self.triggered_list[idx] = True
                    self.email_content_kwargs['log_%s_count' % key.lower()] += ' triggered!!!'
                    if getattr(self, 'LOG_%s_TRIGGER_FORCESTOP' % key):
                        self.flag = '%s_ForceStop' % key if '_ForceStop' not in self.flag else self.flag
                        to_forcestop = True
                    elif getattr(self, 'LOG_%s_TRIGGER_STOP' % key) and not self.has_been_stopped:
                        self.flag = '%s_Stop' % key if 'Stop' not in self.flag else self.flag
                        self.has_been_stopped = True  # Execute 'Stop' one time at most to avoid unclean shutdown
                        to_stop = True
                    elif not self.has_been_stopped:
                        self.flag = '%s_Trigger' % key if not self.flag else self.flag
            if to_forcestop:
                self.logger.debug("%s: %s", self.flag, self.job_key)
                # api(self.node, 'forcestop', self.project, self.job)
                _url = url_for('api', node=self.node, opt='forcestop',
                               project=self.project, version_spider_job=self.job)
                self.get_response_from_view(_url)
            elif to_stop:
                self.logger.debug("%s: %s", self.flag, self.job_key)
                # api(self.node, 'stop', self.project, self.job)
                _url = url_for('api', node=self.node, opt='stop',
                               project=self.project, version_spider_job=self.job)
                self.get_response_from_view(_url)

        if not self.flag and 0 < self.ON_JOB_RUNNING_INTERVAL <= time.time() - self.last_send_timestamp:
            self.flag = 'Running'

    def handle_email_flag(self):
        if self.flag:
            # Send email
            # now_day = date.isoweekday(datetime.now())
            now_day = date.isoweekday(date.today())
            now_hour = datetime.now().hour
            if now_day in self.EMAIL_WORKING_DAYS and now_hour in self.EMAIL_WORKING_HOURS:
                self.EMAIL_KWARGS['subject'] = '%s %s #scrapydweb' % (self.flag, self.job_key)
                self.EMAIL_KWARGS['content'] = self.json_dumps(self.email_content_kwargs, sort_keys=False)

                args = [
                    sys.executable,
                    os.path.join(os.path.dirname(CWD), 'utils', 'send_email.py'),
                    self.json_dumps(self.EMAIL_KWARGS)
                ]
                self.logger.info("Sending email: %s", self.EMAIL_KWARGS['subject'])
                Popen(args)

            # Update self.job_data_dict (last_send_timestamp would be updated only when flag is non-empty)
            self.logger.info("Previous job_data['%s'] %s", self.job_key, self.job_data_dict[self.job_key])
            self.job_data_dict[self.job_key] = (self.job_stats, self.triggered_list, self.has_been_stopped, time.time())
            self.logger.info("Updated  job_data['%s'] %s", self.job_key, self.job_data_dict[self.job_key])

        if self.job_finished:
            self.job_data_dict.pop(self.job_key)
            if len(self.job_finished_set) > 1000:
                self.job_finished_set.clear()
            self.job_finished_set.add(self.job_key)
            self.logger.info('job_finished: %s', self.job_key)
