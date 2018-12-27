# coding: utf8
import re
import time

from .myview import MyView
from .vars import DEFAULT_LATEST_VERSION


API_MAP = dict(start='schedule', stop='cancel', forcestop='cancel')


class ApiView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.opt = self.view_args['opt']
        self.project = self.view_args['project']
        self.version_spider_job = self.view_args['version_spider_job']

        self.url = 'http://{}/{}.json'.format(self.SCRAPYD_SERVER, API_MAP.get(self.opt, self.opt))
        self.data = None

    def dispatch_request(self, **kwargs):
        self.update_url()
        self.update_data()
        return self.generate_response()

    def update_url(self):
        if self.opt in ['listversions', 'listjobs']:
            self.url += '?project=%s' % self.project
        elif self.opt == 'listspiders':
            if self.version_spider_job == DEFAULT_LATEST_VERSION:
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

    def generate_response(self):
        timeout = 5 if self.opt == 'daemonstatus' else 60
        times = 2 if self.opt == 'forcestop' else 1
        status_code = 0
        js = {}
        for __ in range(times):
            status_code, js = self.make_request(self.url, self.data, timeout=timeout, auth=self.AUTH)
            if times != 1:
                js['times'] = times
                time.sleep(2)

        if status_code != 200:
            js['tip'] = "Make sure that your Scrapyd server is accessable."
        elif js['status'] != 'ok':
            if re.search('No such file|no active project', js.get('message', '')):
                js['tip'] = "Maybe the project had been deleted, check out the Manage page."
            elif self.opt == 'listversions':
                js['tip'] = (
                    "Maybe it's caused by failing to compare versions, "
                    "you can check out the HELP section in the Deploy page for more info, "
                    "and solve the problem in the Manage page."
                )
            elif self.opt == 'listspiders' and re.search("TypeError: 'tuple'", js.get('message', '')):
                js['tip'] = "Maybe it's a broken project, check out the Manage page to delete it."

        return self.json_dumps(js)
