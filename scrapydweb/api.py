# coding: utf8
import re
import time

from .myview import MyView


API_MAP = dict(start='schedule', stop='cancel', forcestop='cancel', liststats='logs/stats')


class ApiView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

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
        return self.json_dumps(self.js, sort_keys=False)

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
        timeout = 5 if self.opt == 'daemonstatus' else 60
        json_dumps = False if self.opt in ['daemonstatus', 'liststats'] else True
        times = 2 if self.opt == 'forcestop' else 1
        for __ in range(times):
            self.status_code, self.js = self.make_request(self.url, self.data, auth=self.AUTH,
                                                          api=True, json_dumps=json_dumps, timeout=timeout)
            if times != 1:
                self.js['times'] = times
                time.sleep(2)

    def handle_result(self):
        if self.status_code != 200:
            if self.opt == 'liststats':
                self.js['tip'] = ("'pip install logparser' on the current Scrapyd host "
                                  "and get it started via command 'logparser'")
            else:
                self.js['tip'] = "Make sure that your Scrapyd server is accessable."
        elif self.js['status'] != 'ok':
            if re.search('No such file|no active project', self.js.get('message', '')):
                self.js['tip'] = "Maybe the project had been deleted, check out the Manage page."
            elif self.opt == 'listversions':
                self.js['tip'] = (
                    "Maybe it's caused by failing to compare versions, "
                    "you can check out the HELP section in the Deploy page for more info, "
                    "and solve the problem in the Manage page."
                )
            elif self.opt == 'listspiders' and re.search("TypeError: 'tuple'", self.js.get('message', '')):
                self.js['tip'] = "Maybe it's a broken project, check out the Manage page to delete it."
        elif self.opt == 'liststats' and self.project and self.version_spider_job:
            stats = None
            if self.project in self.js['datas']:
                for spider in self.js['datas'][self.project]:
                    for jobid in self.js['datas'][self.project][spider]:
                        if jobid == self.version_spider_job:
                            stats = self.js['datas'][self.project][spider][self.version_spider_job]
                            self.js['project'] = self.project
                            self.js['spider'] = spider
                            self.js['jobid'] = jobid
                            break
            if not stats:
                stats = dict(pages=self.NA, items=self.NA)
            self.js.setdefault('project', self.project)
            self.js.setdefault('spider', self.NA)
            self.js.setdefault('jobid', self.version_spider_job)
            self.js['stats'] = stats
            self.js.pop('datas')
