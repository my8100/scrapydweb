# coding: utf-8
import re
import time

from .baseview import BaseView


API_MAP = dict(start='schedule', stop='cancel', forcestop='cancel', liststats='logs/stats')


class ApiView(BaseView):

    def __init__(self):
        super(ApiView, self).__init__()

        self.opt = self.view_args['opt']
        self.project = self.view_args['project']
        self.version_spider_job = self.view_args['version_spider_job']

        self.url = 'http://{}/{}.json'.format(self.SCRAPYD_SERVER, API_MAP.get(self.opt, self.opt))
        self.data = None
        self.status_code = 0
        self.js = {}

    def dispatch_request(self, **kwargs):
        self.update_url()
        self.update_data()
        self.get_result()
        self.handle_result()
        return self.json_dumps(self.js, sort_keys=False, as_response=True)

    def update_url(self):
        if self.opt in ['listversions', 'listjobs']:
            self.url += '?project=%s' % self.project
        elif self.opt == 'listspiders':
            if self.version_spider_job == self.DEFAULT_LATEST_VERSION:
                self.url += '?project=%s' % self.project
            else:
                # Should be _version
                self.url += '?project=%s&_version=%s' % (self.project, self.version_spider_job)

    def update_data(self):
        self.data = dict(project=self.project)
        if self.opt == 'start':
            self.data['spider'] = self.version_spider_job
            self.data['jobid'] = self.get_now_string()
        elif self.opt in ['stop', 'forcestop']:
            self.data['job'] = self.version_spider_job
        elif self.opt == 'delversion':
            self.data['version'] = self.version_spider_job
        elif self.opt == 'delproject':
            pass
        else:
            self.data = None

    def get_result(self):
        timeout = 3 if self.opt == 'daemonstatus' else 60
        dumps_json = self.opt not in ['daemonstatus', 'liststats']
        times = 2 if self.opt == 'forcestop' else 1
        for __ in range(times):
            self.status_code, self.js = self.make_request(self.url, data=self.data, auth=self.AUTH,
                                                          as_json=True, dumps_json=dumps_json, timeout=timeout)
            if times != 1:
                self.js['times'] = times
                time.sleep(2)

    def handle_result(self):
        if self.status_code != 200:
            if self.opt == 'liststats':
                if self.project and self.version_spider_job:  # 'List Stats' in the Servers page
                    if self.status_code == 404:
                        self.js = dict(status=self.OK, tip="'pip install logparser' and run command 'logparser'")
                else:  # XMLHttpRequest in the Jobs page; POST in jobs.py
                    self.js['tip'] = ("'pip install logparser' on host '%s' and run command 'logparser' "
                                      "to show crawled_pages and scraped_items. ") % self.SCRAPYD_SERVER
            else:
                self.js['tip'] = "Make sure that your Scrapyd server is accessable. "
        elif self.js['status'] != self.OK:
            if re.search('No such file|no active project', self.js.get('message', '')):
                self.js['tip'] = "Maybe the project had been deleted, check out the Projects page. "
            elif self.opt == 'listversions':
                self.js['tip'] = (
                    "Maybe it's caused by failing to compare versions, "
                    "you can check out the HELP section in the Deploy Project page for more info, "
                    "and solve the problem in the Projects page. "
                )
            elif self.opt == 'listspiders' and re.search("TypeError: 'tuple'", self.js.get('message', '')):
                self.js['tip'] = "Maybe it's a broken project, check out the Projects page to delete it. "
        elif self.opt == 'liststats':
            if self.js.get('logparser_version') != self.LOGPARSER_VERSION:
                if self.project and self.version_spider_job:  # 'List Stats' in the Servers page
                    tip = "'pip install --upgrade logparser' to update LogParser to v%s" % self.LOGPARSER_VERSION
                    self.js = dict(status=self.OK, tip=tip)
                else:  # XMLHttpRequest in the Jobs page; POST in jobs.py
                    self.js['tip'] = ("'pip install --upgrade logparser' on host '%s' and run command 'logparser' "
                                      "to update LogParser to v%s") % (self.SCRAPYD_SERVER, self.LOGPARSER_VERSION)
                    self.js['status'] = self.ERROR
            elif self.project and self.version_spider_job:  # 'List Stats' in the Servers page
                self.extract_pages_items()

    def extract_pages_items(self):
        details = None
        if self.project in self.js['datas']:
            for spider in self.js['datas'][self.project]:
                for jobid in self.js['datas'][self.project][spider]:
                    if jobid == self.version_spider_job:
                        details = self.js['datas'][self.project][spider][self.version_spider_job]
                        self.js['project'] = self.project
                        self.js['spider'] = spider
                        self.js['jobid'] = jobid
                        break
        if not details:
            details = dict(pages=self.NA, items=self.NA)
        details.setdefault('project', self.project)
        details.setdefault('spider', self.NA)
        details.setdefault('jobid', self.version_spider_job)
        details['logparser_version'] = self.js.get('logparser_version', None)
        self.js = dict(status=self.OK, details=details)
