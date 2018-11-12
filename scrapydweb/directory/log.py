# coding: utf8
import os
import sys
import io
import time
from datetime import datetime, date
import re
from collections import OrderedDict
from subprocess import Popen
import traceback

from flask import render_template, url_for, request, send_from_directory, flash

from ..myview import MyView
from ..vars import CACHE_PATH, INFO, WARN, EMAIL_CONTENT_KEYS, EMAIL_TRIGGER_KEYS
from .utils import parse_log


CWD = os.path.dirname(os.path.abspath(__file__))
job_data_dict = {}
# job_finished_set would be updated by caching POST with ?job_finished=True > email_notice() only,
# used for determining whether to show 'refresh' button with '?refresh_cache=True'.
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

        self.job_data_dict = job_data_dict
        self.job_finished_set = job_finished_set

        self.url = u'http://{}/logs/{}/{}/{}.log'.format(self.SCRAPYD_SERVER, self.project, self.spider, self.job)
        self.template_utf8 = 'scrapydweb/simpleui/utf8.html' if self.IS_SIMPLEUI else 'scrapydweb/utf8.html'
        self.template_stats = 'scrapydweb/simpleui/stats.html' if self.IS_SIMPLEUI else 'scrapydweb/stats.html'
        self.status_code = 0
        self.text = ''
        self.spider_path = ''
        self.stats_kwargs = {}
        self.refresh_url = ''
        self.stats_html = ''
        self.utf8_html = ''

        # ([0] * 8, [False] * 6, False, time.time())
        self.job_stats_previous = []
        self.triggered_list = []
        self.has_been_stopped = False
        self.last_send_timestamp = 0
        self.job_stats = []
        self.job_stats_diff = []
        self.email_content_kwargs = {}
        self.flag = ''

        # In Logs page: xxx.log/?with_ext=True
        if request.args.get('with_ext', ''):
            self.SCRAPYD_LOG_EXTENSIONS = ['']

        self.job_key = '/%s/%s/%s/%s' % (self.node, self.project, self.spider, self.job)

        # request from caching would post ?job_finished=True for finished job,
        # as well as links of finished job in Dashboard page
        self.JOB_FINISHED = True if request.args.get('job_finished', '') else False

        # Three conditions in total
        self.disable_cache = self.IS_SIMPLEUI or not self.CACHE_ENABLED
        _condition = request.args.get('refresh_cache') or self.POST  # scrapydweb/utils/cache.py would use 'POST'
        self.to_refresh_cache = True if not self.disable_cache and _condition else False
        self.to_read_cache = True if not self.disable_cache and not self.to_refresh_cache else False

    def dispatch_request(self, **kwargs):
        if not self.disable_cache:
            self.mkdir_spider_path()

        # Return cached html
        if self.to_read_cache:
            htmlname = '%s_%s.html' % (self.job, self.opt)
            if os.path.exists(os.path.join(self.spider_path, htmlname)):
                return send_from_directory(self.spider_path, htmlname)

        # Try to read local scrapy log file
        if self.SCRAPYD_SERVER.split(':')[0] == '127.0.0.1' and self.SCRAPYD_LOGS_DIR:
            self.read_local_scrapy_log()

        # Has to request scrapy log
        if not self.text:
            self.request_scrapy_log()
            if self.status_code != 200:
                return render_template(self.template_result, node=self.node,
                                       url=self.url, status_code=self.status_code, text=self.text)

        self.render_stats_html()
        self.render_utf8_html()
        if not self.disable_cache:
            self.save_html()

        if self.EMAIL_ENABLED and self.POST:  # only cache.py would make POST request
            self.email_notice()

        return self.stats_html if self.opt == 'stats' else self.utf8_html

    def mkdir_spider_path(self):
        node_path = os.path.join(CACHE_PATH, re.sub(r'[.:]', '_', self.SCRAPYD_SERVER))
        project_path = os.path.join(node_path, self.project)
        self.spider_path = os.path.join(project_path, self.spider)

        if not os.path.isdir(CACHE_PATH):
            os.mkdir(CACHE_PATH)
        if not os.path.isdir(node_path):
            os.mkdir(node_path)
        if not os.path.isdir(project_path):
            os.mkdir(project_path)
        if not os.path.isdir(self.spider_path):
            os.mkdir(self.spider_path)

    def read_local_scrapy_log(self):
        file_found = False
        logfile = ''
        for ext in self.SCRAPYD_LOG_EXTENSIONS:
            logfile = os.path.join(self.SCRAPYD_LOGS_DIR, self.project, self.spider, self.job + ext)
            if os.path.exists(logfile):
                with io.open(logfile, 'r', encoding='utf-8', errors='ignore') as f:
                    self.text = f.read()
                flash("Using local scrapy logfile: %s" % logfile, INFO)
                file_found = True
                break
        if not file_found:
            flash("Local logfile '%s' NOT found, making request to Scrapyd server instead" % logfile, WARN)

    def request_scrapy_log(self):
        url_without_ext = re.sub(r'.log$', '', self.url)

        for ext in self.SCRAPYD_LOG_EXTENSIONS:
            self.url = '%s%s' % (url_without_ext, ext)
            self.status_code, self.text = self.make_request(self.url, api=False, auth=self.AUTH)
            if self.status_code == 200:
                break

    def render_stats_html(self):
        url_utf8 = request.url.replace('/log/stats/', '/log/utf8/').replace('refresh_cache=True', 'refresh_cache=')
        self.stats_kwargs = dict(
            project=self.project,
            spider=self.spider,
            job=self.job,
            url_source=self.url,
            url_utf8=url_utf8,
            LAST_LOG_ALERT_SECONDS=self.LAST_LOG_ALERT_SECONDS
        )

        parse_log(self.text, self.stats_kwargs)

        # To show 'refresh' button with '?refresh_cache=True'
        if (not self.disable_cache
           and not self.stats_kwargs.get('finish_reason')
           and not self.JOB_FINISHED
           and self.job_key not in self.job_finished_set):
            # http://flask.pocoo.org/docs/1.0/api/#flask.Request.url_root
            _query_string = '?refresh_cache=True' + ('&ui=simple' if self.IS_SIMPLEUI else '')
            self.refresh_url = request.script_root + request.path + _query_string
        else:
            self.refresh_url = ''

        self.stats_kwargs['refresh_url'] = self.refresh_url.replace('/log/utf8/', '/log/stats/')
        self.stats_kwargs['last_refresh_timestamp'] = time.time()
        self.stats_html = render_template(self.template_stats, node=self.node, **self.stats_kwargs)

    def render_utf8_html(self):
        url_stats = request.url.replace('/log/utf8/', '/log/stats/').replace('refresh_cache=True', 'refresh_cache=')
        utf8_kwargs = dict(
            node=self.node,
            project=self.project,
            spider=self.spider,
            url_source=self.url,
            url_stats=url_stats,
            refresh_url=self.refresh_url.replace('/log/stats/', '/log/utf8/'),
            last_refresh_timestamp=time.time(),
            LAST_LOG_ALERT_SECONDS=self.LAST_LOG_ALERT_SECONDS,
            text=self.text
        )

        self.utf8_html = render_template(self.template_utf8, **utf8_kwargs)

    def save_html(self):
        for opt_, html in zip(['stats', 'utf8'], [self.stats_html, self.utf8_html]):
            htmlname = '%s_%s.html' % (self.job, opt_)
            htmlpath = os.path.join(self.spider_path, htmlname)
            try:
                with io.open(htmlpath, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(html)
            except Exception as err:
                self.logger.error("Fail to cache HTML to %s: %s" % (htmlpath, err))
                try:
                    os.remove(htmlpath)
                except:
                    pass

    def email_notice(self):
        if not (date.isoweekday(datetime.now()) in self.EMAIL_WORKING_DAYS
           and datetime.now().hour in self.EMAIL_WORKING_HOURS):
            return

        try:
            self.send_email()
        except:
            self.logger.error(traceback.format_exc())

    def send_email(self):
        job_data_default = ([0] * 8, [False] * 6, False, time.time())
        job_data = self.job_data_dict.setdefault(self.job_key, job_data_default)
        (self.job_stats_previous, self.triggered_list, self.has_been_stopped, self.last_send_timestamp) = job_data
        # print(self.job_data_dict)
        self.job_stats = [self.stats_kwargs['re_matches'][i]['count'] for i in range(6)]
        self.job_stats.extend([self.stats_kwargs['crawled_pages'], self.stats_kwargs['scraped_items']])
        self.job_stats_diff = [j - i for i, j in zip(self.job_stats_previous, self.job_stats)]

        self.set_email_content_kwargs()
        self.set_flag()
        self.handle_flag()

    def set_email_content_kwargs(self):
        # For compatibility with Python 2, use OrderedDict() to keep insertion order
        self.email_content_kwargs = OrderedDict()
        self.email_content_kwargs['SCRAPYD_SERVER'] = self.SCRAPYD_SERVER
        self.email_content_kwargs['project'] = self.stats_kwargs['project']
        self.email_content_kwargs['spider'] = self.stats_kwargs['spider']
        self.email_content_kwargs['job'] = self.stats_kwargs['job']
        self.email_content_kwargs['start_time'] = self.stats_kwargs['first_log_time']
        self.email_content_kwargs['latest_log_time'] = self.stats_kwargs['latest_log_time']
        self.email_content_kwargs['elasped'] = self.stats_kwargs['elasped']
        self.email_content_kwargs['finish_reason'] = self.stats_kwargs['finish_reason'] or 'NOT found in log'
        self.email_content_kwargs['url_stats'] = request.url

        for idx, i in enumerate(EMAIL_CONTENT_KEYS):
            if self.job_stats_diff[idx]:
                self.email_content_kwargs[i] = '%s + %s' % (self.job_stats_previous[idx], self.job_stats_diff[idx])
            else:
                self.email_content_kwargs[i] = self.job_stats[idx]

        _bind = '127.0.0.1' if self.SCRAPYDWEB_BIND == '0.0.0.0' else self.SCRAPYDWEB_BIND
        _url_stop = url_for('api', node=self.node, opt='stop', project=self.project, version_spider_job=self.job)
        self.email_content_kwargs['url_stop'] = 'http://%s:%s%s' % (_bind, self.SCRAPYDWEB_PORT, _url_stop)

        now_timestamp = time.time()
        latest_crawl_diff = now_timestamp - self.stats_kwargs['latest_crawl_timestamp']
        latest_scrape_diff = now_timestamp - self.stats_kwargs['latest_scrape_timestamp']
        latest_log_diff = now_timestamp - self.stats_kwargs['latest_log_timestamp']
        self.email_content_kwargs['latest_crawl'] = "%s seconds ago" % int(latest_crawl_diff)
        self.email_content_kwargs['latest_scrape'] = "%s seconds ago" % int(latest_scrape_diff)
        self.email_content_kwargs['latest_log'] = "%s seconds ago" % int(latest_log_diff)
        self.email_content_kwargs['current_time'] = time.ctime()

    def set_flag(self):
        if self.ON_JOB_FINISHED and self.JOB_FINISHED:
            self.flag = 'Finished'
        elif not all(self.triggered_list):
            to_forcestop = False
            to_stop = False
            # The order of the elements in EMAIL_TRIGGER_KEYS matters:
            # ['CRITICAL', 'ERROR', 'WARNING', 'REDIRECT', 'RETRY', 'IGNORE']
            for idx, key in enumerate(EMAIL_TRIGGER_KEYS):
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
                self.logger.debug("%s: %s" % (self.flag, self.job_key))
                # api(self.node, 'forcestop', self.project, self.job)
                _url = url_for('api', node=self.node, opt='forcestop',
                               project=self.project, version_spider_job=self.job)
                self.get_response_from_view(_url)
            elif to_stop:
                self.logger.debug("%s: %s" % (self.flag, self.job_key))
                # api(self.node, 'stop', self.project, self.job)
                _url = url_for('api', node=self.node, opt='stop',
                               project=self.project, version_spider_job=self.job)
                self.get_response_from_view(_url)

        if not self.flag and 0 < self.ON_JOB_RUNNING_INTERVAL <= time.time() - self.last_send_timestamp:
            self.flag = 'Running'

    def handle_flag(self):
        if self.flag:
            # Send email
            self.EMAIL_KWARGS['subject'] = '%s %s' % (self.flag, self.job_key)
            self.EMAIL_KWARGS['content'] = self.json_dumps(self.email_content_kwargs, sort_keys=False)

            args = [
                sys.executable,
                os.path.join(os.path.dirname(CWD), 'utils', 'send_email.py'),
                self.json_dumps(self.EMAIL_KWARGS)
            ]
            self.logger.info("Sending email: %s" % self.EMAIL_KWARGS['subject'])
            Popen(args)

            # Update self.job_data_dict (last_send_timestamp would be updated only when flag is non-empty)
            self.logger.debug(self.job_data_dict[self.job_key])
            self.job_data_dict[self.job_key] = (self.job_stats, self.triggered_list, self.has_been_stopped, time.time())
            self.logger.debug(self.job_data_dict[self.job_key])

        if self.JOB_FINISHED:
            self.job_data_dict.pop(self.job_key)
            if len(self.job_finished_set) > 1000:
                self.job_finished_set.clear()
            self.job_finished_set.add(self.job_key)
