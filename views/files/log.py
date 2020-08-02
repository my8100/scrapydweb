# coding: utf-8
from collections import OrderedDict, defaultdict
from datetime import date, datetime
import io
import json
import os
import re
from subprocess import Popen
import sys
import tarfile
import time

from flask import flash, get_flashed_messages, render_template, request, url_for
from logparser import parse

from ...vars import ROOT_DIR
from ..baseview import BaseView


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
# job_finished_key_dict would only be updated by poll POST with ?job_finished=True > monitor_alert(),
# used for determining whether to show 'click to refresh' button in the Log and Stats page.
job_finished_key_dict = defaultdict(OrderedDict)
# For /log/report/
job_finished_report_dict = defaultdict(OrderedDict)
REPORT_KEYS_SET = {'from_memory', 'status', 'pages', 'items', 'shutdown_reason', 'finish_reason', 'runtime',
                   'first_log_time', 'latest_log_time', 'log_categories', 'latest_matches'}


# http://flask.pocoo.org/docs/1.0/api/#flask.views.View
# http://flask.pocoo.org/docs/1.0/views/
class LogView(BaseView):

    def __init__(self):
        super(LogView, self).__init__()  # super().__init__()

        self.opt = self.view_args['opt']
        self.project = self.view_args['project']
        self.spider = self.view_args['spider']
        self.job = self.view_args['job']

        self.job_key = '/%s/%s/%s/%s' % (self.node, self.project, self.spider, self.job)

        # Note that self.LOCAL_SCRAPYD_LOGS_DIR may be an empty string
        # Extension like '.log' is excluded here.
        self.url = u'http://{}/logs/{}/{}/{}'.format(self.SCRAPYD_SERVER, self.project, self.spider, self.job)
        self.log_path = os.path.join(self.LOCAL_SCRAPYD_LOGS_DIR, self.project, self.spider, self.job)

        # For Log and Stats buttons in the Logs page: /a.log/?with_ext=True
        self.with_ext = request.args.get('with_ext', None)
        if self.with_ext:
            self.SCRAPYD_LOG_EXTENSIONS = ['']
            job_without_ext = self.get_job_without_ext(self.job)
        else:
            job_without_ext = self.job

        # json file by LogParser
        self.json_path = os.path.join(self.LOCAL_SCRAPYD_LOGS_DIR, self.project, self.spider, job_without_ext+'.json')
        self.json_url = u'http://{}/logs/{}/{}/{}.json'.format(self.SCRAPYD_SERVER, self.project, self.spider,
                                                               job_without_ext)

        self.status_code = 0
        self.text = ''
        if self.opt == 'report':
            self.template = None
        else:
            self.template = 'scrapydweb/%s%s.html' % (self.opt, '_mobileui' if self.USE_MOBILEUI else '')
        self.kwargs = dict(node=self.node, project=self.project, spider=self.spider,
                           job=job_without_ext, url_refresh='', url_jump='')

        # Request that comes from poll POST for finished job and links of finished job in the Jobs page
        # would be attached with the query string '?job_finished=True'
        self.job_finished = request.args.get('job_finished', None)

        self.utf8_realtime = False
        self.stats_realtime = False
        self.stats_logparser = False
        self.report_logparser = False
        if self.opt == 'utf8':
            flash("It's recommended to check out the latest log via: the Stats page >> View log >> Tail", self.WARN)
            self.utf8_realtime = True
        elif self.opt == 'stats':
            self.stats_realtime = True if request.args.get('realtime', None) else False
            self.stats_logparser = not self.stats_realtime
        else:
            self.report_logparser = True
        self.logparser_valid = False
        self.backup_stats_valid = False
        spider_path = self.mkdir_spider_path()
        self.backup_stats_path = os.path.join(spider_path, job_without_ext + '.json')
        self.stats = {}

        # job_data for monitor & alert: ([0] * 8, [False] * 6, False, time.time())
        self.job_stats_previous = []
        self.triggered_list = []
        self.has_been_stopped = False
        self.last_send_timestamp = 0
        self.job_stats = []
        self.job_stats_diff = []
        # For compatibility with Python 2, use OrderedDict() to keep insertion order
        self.email_content_kwargs = OrderedDict()
        self.flag = ''

        self.jobs_to_keep = self.JOBS_FINISHED_JOBS_LIMIT or 200

    def dispatch_request(self, **kwargs):
        if self.report_logparser:
            self.read_stats_for_report()
        # Try to request stats by LogParser to avoid reading/requesting the whole log
        if not self.logparser_valid and (self.stats_logparser or self.report_logparser):
            if self.IS_LOCAL_SCRAPYD_SERVER and self.LOCAL_SCRAPYD_LOGS_DIR:
                self.read_local_stats_by_logparser()
            if not self.logparser_valid:
                self.request_stats_by_logparser()

        if not self.logparser_valid and not self.text:
            # Try to read local logfile
            if self.IS_LOCAL_SCRAPYD_SERVER and self.LOCAL_SCRAPYD_LOGS_DIR:
                self.read_local_scrapy_log()
            # Has to request scrapy logfile
            if not self.text:
                self.request_scrapy_log()
                if self.status_code != 200:
                    if self.stats_logparser or self.report_logparser:
                        self.load_backup_stats()
                    if not self.backup_stats_valid:
                        if not self.report_logparser:
                            kwargs = dict(node=self.node, url=self.url, status_code=self.status_code, text=self.text)
                            return render_template(self.template_fail, **kwargs)
            else:
                self.url += self.SCRAPYD_LOG_EXTENSIONS[0]
        else:
            self.url += self.SCRAPYD_LOG_EXTENSIONS[0]

        if (not self.utf8_realtime
            and not self.logparser_valid
            and self.text
            and self.status_code in [0, 200]):
            self.logger.warning('Parse the whole log')
            self.stats = parse(self.text)
            # Note that the crawler_engine is not available when using parse()
            self.stats.setdefault('crawler_engine', {})
            self.stats.setdefault('status', self.OK)

        if self.report_logparser:
            if self.stats and not self.stats.setdefault('from_memory', False):
                self.simplify_stats_for_report()
                self.keep_stats_for_report()
            get_flashed_messages()
            # 0, -1, 404 load backup
            if self.status_code < 100 or self.stats:
                status_code = 200
            else:
                status_code = self.status_code
            return self.json_dumps(self.stats or dict(status='error'), as_response=True), status_code
        else:
            self.update_kwargs()
            if self.ENABLE_MONITOR and self.POST:  # Only poll.py would make POST request
                self.monitor_alert()
            return render_template(self.template, **self.kwargs)

    def read_local_stats_by_logparser(self):
        self.logger.debug("Try to read local stats by LogParser: %s", self.json_path)
        try:
            with io.open(self.json_path, 'r', encoding='utf-8') as f:
                js = json.loads(f.read())
        except Exception as err:
            self.logger.error("Fail to read local stats from %s: %s", self.json_path, err)
            return
        else:
            if js.get('logparser_version') != self.LOGPARSER_VERSION:
                msg = "Mismatching logparser_version %s in local stats" % js.get('logparser_version')
                self.logger.warning(msg)
                flash(msg, self.WARN)
                return
            self.logparser_valid = True
            self.stats = js
            msg = "Using local stats: LogParser v%s, last updated at %s, %s" % (
                js['logparser_version'], js['last_update_time'], self.handle_slash(self.json_path))
            self.logger.info(msg)
            flash(msg, self.INFO)

    def request_stats_by_logparser(self):
        self.logger.debug("Try to request stats by LogParser: %s", self.json_url)
        # self.make_request() would check the value of key 'status' if as_json=True
        status_code, js = self.make_request(self.json_url, auth=self.AUTH, as_json=True, dumps_json=False)
        if status_code != 200:
            self.logger.error("Fail to request stats from %s, got status_code: %s", self.json_url, status_code)
            if self.IS_LOCAL_SCRAPYD_SERVER and self.ENABLE_LOGPARSER:
                flash("Request to %s got code %s, wait until LogParser parses the log. " % (self.json_url, status_code),
                      self.INFO)
            else:
                flash(("'pip install logparser' on host '%s' and run command 'logparser'. "
                       "Or wait until LogParser parses the log. ") % self.SCRAPYD_SERVER, self.WARN)
            return
        elif js.get('logparser_version') != self.LOGPARSER_VERSION:
            msg = "'pip install --upgrade logparser' on host '%s' to update LogParser to v%s" % (
                self.SCRAPYD_SERVER, self.LOGPARSER_VERSION)
            self.logger.warning(msg)
            flash(msg, self.WARN)
            return
        else:
            self.logparser_valid = True
            # TODO: dirty data
            self.stats = js
            msg = "LogParser v%s, last updated at %s, %s" % (
                js['logparser_version'], js['last_update_time'], self.json_url)
            self.logger.info(msg)
            flash(msg, self.INFO)

    def read_local_scrapy_log(self):
        for ext in self.SCRAPYD_LOG_EXTENSIONS:
            log_path = self.log_path + ext
            if os.path.exists(log_path):
                if tarfile.is_tarfile(log_path):
                    self.logger.debug("Ignore local tarfile and use requests instead: %s", log_path)
                    break
                with io.open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    self.text = f.read()
                log_path = self.handle_slash(log_path)
                msg = "Using local logfile: %s" % log_path
                self.logger.debug(msg)
                flash(msg, self.INFO)
                break

    def request_scrapy_log(self):
        for ext in self.SCRAPYD_LOG_EXTENSIONS:
            url = self.url + ext
            self.status_code, self.text = self.make_request(url, auth=self.AUTH, as_json=False)
            if self.status_code == 200:
                self.url = url
                self.logger.debug("Got logfile from %s", self.url)
                break
        else:
            msg = "Fail to request logfile from %s with extensions %s" % (self.url, self.SCRAPYD_LOG_EXTENSIONS)
            self.logger.error(msg)
            flash(msg, self.WARN)
            self.url += self.SCRAPYD_LOG_EXTENSIONS[0]

    def simplify_stats_for_report(self):
        for key in list(self.stats.keys()):
            if key not in REPORT_KEYS_SET:
                self.stats.pop(key)
        try:
            for key in self.stats['log_categories']:
                self.stats['log_categories'][key] = dict(count=self.stats['log_categories'][key]['count'])
        except KeyError:
            pass
        try:
            self.stats['latest_matches'] = dict(latest_item=self.stats['latest_matches']['latest_item'])
        except KeyError:
            pass

    def keep_stats_for_report(self):
        od = job_finished_report_dict[self.node]
        if self.job_key in od:
            return
        if (self.stats.get('shutdown_reason', self.NA) == self.NA
            and self.stats.get('finish_reason', self.NA) == self.NA):
            return
        if set(self.stats.keys()) == REPORT_KEYS_SET:
            od[self.job_key] = self.stats
            if len(od) > self.jobs_to_keep:
                od.popitem(last=False)
            self.logger.debug("%s keys in job_finished_report_dict[%s]", len(od), self.node)

    def read_stats_for_report(self):
        try:
            self.stats = job_finished_report_dict[self.node][self.job_key]
        except KeyError:
            self.logger.debug("%s not found in job_finished_report_dict[%s]", self.job_key, self.node)
        else:
            self.logger.debug("%s found in job_finished_report_dict[%s]", self.job_key, self.node)
            self.logparser_valid = True
            self.stats['from_memory'] = True

    def mkdir_spider_path(self):
        node_path = os.path.join(self.STATS_PATH,
                                 re.sub(self.LEGAL_NAME_PATTERN, '-', re.sub(r'[.:]', '_', self.SCRAPYD_SERVER)))
        project_path = os.path.join(node_path, self.project)
        spider_path = os.path.join(project_path, self.spider)

        if not os.path.isdir(self.STATS_PATH):
            os.mkdir(self.STATS_PATH)
        if not os.path.isdir(node_path):
            os.mkdir(node_path)
        if not os.path.isdir(project_path):
            os.mkdir(project_path)
        if not os.path.isdir(spider_path):
            os.mkdir(spider_path)
        return spider_path

    def backup_stats(self):
        # TODO: delete backup stats json file when the job is deleted in the Jobs page with database view
        try:
            with io.open(self.backup_stats_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(self.json_dumps(self.stats))
        except Exception as err:
            self.logger.error("Fail to backup stats to %s: %s" % (self.backup_stats_path, err))
            try:
                os.remove(self.backup_stats_path)
            except:
                pass
        else:
            self.logger.info("Saved backup stats to %s", self.backup_stats_path)

    def load_backup_stats(self):
        self.logger.debug("Try to load backup stats by LogParser: %s", self.json_path)
        try:
            with io.open(self.backup_stats_path, 'r', encoding='utf-8') as f:
                js = json.loads(f.read())
        except Exception as err:
            self.logger.error("Fail to load backup stats from %s: %s", self.backup_stats_path, err)
        else:
            if js.get('logparser_version') != self.LOGPARSER_VERSION:
                msg = "Mismatching logparser_version %s in backup stats" % js.get('logparser_version')
                self.logger.warning(msg)
                flash(msg, self.WARN)
                return
            self.logparser_valid = True
            self.backup_stats_valid = True
            self.stats = js
            msg = "Using backup stats: LogParser v%s, last updated at %s, %s" % (
                js['logparser_version'], js['last_update_time'], self.handle_slash(self.backup_stats_path))
            self.logger.info(msg)
            flash(msg, self.WARN)

    @staticmethod
    def get_ordered_dict(adict):
        # 'source', 'last_update_time', 'last_update_timestamp', other keys in order
        odict = OrderedDict()
        for k in ['source', 'last_update_time', 'last_update_timestamp']:
            odict[k] = adict.pop(k)
        for k in sorted(adict.keys()):
            odict[k] = adict[k]
        return odict

    def update_kwargs(self):
        if self.utf8_realtime:
            self.kwargs['text'] = self.text
            self.kwargs['last_update_timestamp'] = time.time()
            if self.job_finished or self.job_key in job_finished_key_dict[self.node]:
                self.kwargs['url_refresh'] = ''
            else:
                self.kwargs['url_refresh'] = 'javascript:location.reload(true);'
        else:
            # Parsed data comes from json.loads, for compatibility with Python 2,
            # use str(time_) to avoid [u'2019-01-01 00:00:01', 0, 0, 0, 0] in JavaScript.
            for d in self.stats['datas']:
                d[0] = str(d[0])
            # For sorted orders in stats.html with Python 2
            for k in ['crawler_stats', 'crawler_engine']:
                if self.stats[k]:
                    self.stats[k] = self.get_ordered_dict(self.stats[k])

            if self.BACKUP_STATS_JSON_FILE:
                self.backup_stats()
            self.kwargs.update(self.stats)

            if (self.kwargs['finish_reason'] == self.NA
               and not self.job_finished
               and self.job_key not in job_finished_key_dict[self.node]):
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
            if self.SCRAPYD_SERVER_PUBLIC_URL:
                self.kwargs['url_source'] = re.sub(r'^http.*?/logs/', self.SCRAPYD_SERVER_PUBLIC_URL + '/logs/',
                                                   self.url)
            else:
                self.kwargs['url_source'] = self.url
            self.kwargs['url_opt_opposite'] = url_for('log', node=self.node,
                                                      opt='utf8' if self.opt == 'stats' else 'stats',
                                                      project=self.project, spider=self.spider, job=self.job,
                                                      job_finished=self.job_finished, with_ext=self.with_ext,
                                                      ui=self.UI)

    # TODO: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-x-email-support
    def monitor_alert(self):
        job_data_default = ([0] * 8, [False] * 6, False, time.time())
        job_data = job_data_dict.setdefault(self.job_key, job_data_default)
        (self.job_stats_previous, self.triggered_list, self.has_been_stopped, self.last_send_timestamp) = job_data
        self.logger.debug(job_data_dict)
        self.job_stats = [self.kwargs['log_categories'][k.lower() + '_logs']['count']
                          for k in self.ALERT_TRIGGER_KEYS]
        self.job_stats.extend([self.kwargs['pages'] or 0, self.kwargs['items'] or 0])  # May be None by LogParser
        self.job_stats_diff = [j - i for i, j in zip(self.job_stats_previous, self.job_stats)]

        self.set_email_content_kwargs()
        self.set_monitor_flag()
        self.send_alert()
        self.handle_data()

    def set_email_content_kwargs(self):
        self.email_content_kwargs['SCRAPYD_SERVER'] = self.SCRAPYD_SERVER
        self.email_content_kwargs['project'] = self.kwargs['project']
        self.email_content_kwargs['spider'] = self.kwargs['spider']
        self.email_content_kwargs['job'] = self.kwargs['job']
        self.email_content_kwargs['first_log_time'] = self.kwargs['first_log_time']
        self.email_content_kwargs['latest_log_time'] = self.kwargs['latest_log_time']
        self.email_content_kwargs['runtime'] = self.kwargs['runtime']
        self.email_content_kwargs['shutdown_reason'] = self.kwargs['shutdown_reason']
        self.email_content_kwargs['finish_reason'] = self.kwargs['finish_reason']
        self.email_content_kwargs['url_stats'] = request.url + '%sui=mobile' % '&' if request.args else '?'

        for idx, key in enumerate(EMAIL_CONTENT_KEYS):
            if self.job_stats_diff[idx]:
                self.email_content_kwargs[key] = '%s + %s' % (self.job_stats_previous[idx], self.job_stats_diff[idx])
            else:
                self.email_content_kwargs[key] = self.job_stats[idx]
        # pages and items may be None by LogParser
        if self.kwargs['pages'] is None:
            self.email_content_kwargs['crawled_pages'] = self.NA
        if self.kwargs['items'] is None:
            self.email_content_kwargs['scraped_items'] = self.NA

        _url_stop = url_for('api', node=self.node, opt='stop', project=self.project, version_spider_job=self.job)
        self.email_content_kwargs['url_stop'] = self.URL_SCRAPYDWEB + _url_stop

        now_timestamp = time.time()
        for k in ['latest_crawl', 'latest_scrape', 'latest_log']:
            ts = self.kwargs['%s_timestamp' % k]
            self.email_content_kwargs[k] = self.NA if ts == 0 else "%s secs ago" % int(now_timestamp - ts)

        self.email_content_kwargs['current_time'] = self.get_now_string(True)
        self.email_content_kwargs['logparser_version'] = self.kwargs['logparser_version']
        self.email_content_kwargs['latest_item'] = self.kwargs['latest_matches']['latest_item'] or self.NA
        self.email_content_kwargs['Crawler.stats'] = self.kwargs['crawler_stats']
        self.email_content_kwargs['Crawler.engine'] = self.kwargs['crawler_engine']

    def set_monitor_flag(self):
        if self.ON_JOB_FINISHED and self.job_finished:
            self.flag = 'Finished'
        elif not all(self.triggered_list):
            to_forcestop = False
            to_stop = False
            # The order of the elements in ALERT_TRIGGER_KEYS matters:
            # ['CRITICAL', 'ERROR', 'WARNING', 'REDIRECT', 'RETRY', 'IGNORE']
            for idx, key in enumerate(self.ALERT_TRIGGER_KEYS):
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
                _url = url_for('api', node=self.node, opt='forcestop',
                               project=self.project, version_spider_job=self.job)
                self.get_response_from_view(_url)
            elif to_stop:
                self.logger.debug("%s: %s", self.flag, self.job_key)
                _url = url_for('api', node=self.node, opt='stop',
                               project=self.project, version_spider_job=self.job)
                self.get_response_from_view(_url)

        if not self.flag and 0 < self.ON_JOB_RUNNING_INTERVAL <= time.time() - self.last_send_timestamp:
            self.flag = 'Running'

    def send_alert(self):
        if (self.flag
            and date.isoweekday(date.today()) in self.ALERT_WORKING_DAYS  # date.isoweekday(datetime.now())
            and datetime.now().hour in self.ALERT_WORKING_HOURS
        ):
            kwargs = dict(
                flag=self.flag,
                pages=self.NA if self.kwargs['pages'] is None else self.kwargs['pages'],
                items=self.NA if self.kwargs['items'] is None else self.kwargs['items'],
                job_key=self.job_key,
                latest_item=self.kwargs['latest_matches']['latest_item'][:100] or self.NA
            )
            subject = u"{flag} [{pages}p, {items}i] {job_key} {latest_item} #scrapydweb".format(**kwargs)
            self.EMAIL_KWARGS['subject'] = subject
            self.EMAIL_KWARGS['content'] = self.json_dumps(self.email_content_kwargs, sort_keys=False)

            data = dict(
                subject=subject,
                url_stats=self.email_content_kwargs['url_stats'],
                url_stop=self.email_content_kwargs['url_stop'],
                when=self.get_now_string(True),
            )
            if self.ENABLE_SLACK_ALERT:
                self.logger.info("Sending alert via Slack: %s", subject)
                _url = url_for('sendtextapi', opt='slack', channel_chatid_subject=None, text=None)
                self.get_response_from_view(_url, data=data)
            if self.ENABLE_TELEGRAM_ALERT:
                self.logger.info("Sending alert via Telegram: %s", subject)
                _url = url_for('sendtextapi', opt='telegram', channel_chatid_subject=None, text=None)
                self.get_response_from_view(_url, data=data)
            if self.ENABLE_EMAIL_ALERT:
                self.logger.info("Sending alert via Email: %s", subject)
                args = [
                    sys.executable,
                    os.path.join(ROOT_DIR, 'utils', 'send_email.py'),
                    self.json_dumps(self.EMAIL_KWARGS, ensure_ascii=True)
                ]
                Popen(args)

    def handle_data(self):
        if self.flag:
            # Update job_data_dict (last_send_timestamp would be updated only when flag is non-empty)
            self.logger.debug("Previous job_data['%s'] %s", self.job_key, job_data_dict[self.job_key])
            job_data_dict[self.job_key] = (self.job_stats, self.triggered_list, self.has_been_stopped, time.time())
            self.logger.debug("Updated  job_data['%s'] %s", self.job_key, job_data_dict[self.job_key])

        if self.job_finished:
            job_data_dict.pop(self.job_key)
            od = job_finished_key_dict[self.node]
            od[self.job_key] = None
            if len(od) > self.jobs_to_keep:
                od.popitem(last=False)
            self.logger.info('job_finished: %s', self.job_key)
