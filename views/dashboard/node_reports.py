# coding: utf-8
import json

from flask import render_template, url_for

from ..baseview import BaseView


class NodeReportsView(BaseView):

    def __init__(self):
        super(NodeReportsView, self).__init__()

        self.url = url_for('jobs', node=self.node, listjobs='True')
        self.text = ''
        self.jobs = []
        self.pending_jobs = []
        self.running_jobs = []
        self.finished_jobs = []
        self.template = 'scrapydweb/node_reports.html'

    def dispatch_request(self, **kwargs):
        self.text = self.get_response_from_view(self.url, as_json=False)
        try:
            self.jobs = json.loads(self.text)
        except ValueError as err:
            self.logger.error("Fail to decode json from %s: %s", self.url, err)
            return self.text

        for job in self.jobs:
            if not job['start']:
                self.pending_jobs.append(job)
            else:
                if job['finish']:
                    self.finished_jobs.append(job)
                else:
                    self.running_jobs.append(job)

        if self.JOBS_FINISHED_JOBS_LIMIT > 0:
            self.finished_jobs = self.finished_jobs[::-1][:self.JOBS_FINISHED_JOBS_LIMIT]
        else:
            self.finished_jobs = self.finished_jobs[::-1]
        kwargs = dict(
            node=self.node,
            url=self.url,
            pending_jobs=self.pending_jobs,
            running_jobs=self.running_jobs,
            finished_jobs=self.finished_jobs,
            url_report=url_for('log', node=self.node, opt='report', project='PROJECT_PLACEHOLDER',
                               spider='SPIDER_PLACEHOLDER', job='JOB_PLACEHOLDER'),
            url_schedule=url_for('schedule', node=self.node),
        )
        return render_template(self.template, **kwargs)
