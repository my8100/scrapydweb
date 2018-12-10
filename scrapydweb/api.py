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
        # if self.node < 1 or self.node > len(self.SCRAPYD_SERVERS):
            # message = 'node index %s error, which should be between 1 and %s' % (self.node, len(self.SCRAPYD_SERVERS))
            # self.logger.error('!!!!! %s' % message)
            # return self.json_dumps(dict(status_code=-1, status='error', message=message), sort_keys=False)

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
        js = {}
        for __ in range(times):
            status_code, js = self.make_request(self.url, self.data, timeout=timeout, auth=self.AUTH)
            if times != 1:
                js['times'] = times
                time.sleep(2)

        if js['status'] != 'ok':
            if self.opt == 'listversions':
                js['info'] = (
                    "Maybe it's caused by failing to compare versions, "
                    "you can check out the INFO section in the Deploy page, "
                    "and solve the problem in the Manage page."
                )
            elif self.opt == 'listspiders' or re.search('no active project', js.get('message', '')):
                js['info'] = "Maybe the project has been deleted, check out the Manage page"

        return self.json_dumps(js)
