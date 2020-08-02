# coding: utf-8
from flask import redirect, render_template, url_for

from ..baseview import BaseView


metadata = dict(
    project='',
    spider='',
    job='',
    selected_nodes=[]
)


class ClusterReportsView(BaseView):

    def __init__(self):
        super(ClusterReportsView, self).__init__()

        self.project = self.view_args['project'] or metadata['project']
        self.spider = self.view_args['spider'] or metadata['spider']
        self.job = self.view_args['job'] or metadata['job']
        self.selected_nodes = self.get_selected_nodes() or metadata['selected_nodes']
        metadata['project'] = self.project
        metadata['spider'] = self.spider
        metadata['job'] = self.job
        metadata['selected_nodes'] = self.selected_nodes

        self.template = 'scrapydweb/cluster_reports.html'

    def dispatch_request(self, **kwargs):
        if all([self.project, self.spider, self.job]):
            # Click reports memu for the second time
            if not any([self.view_args['project'], self.view_args['spider'], self.view_args['job']]):
                return redirect(url_for('clusterreports', node=self.node, project=self.project,
                                        spider=self.spider, job=self.job))
            # Click reports button on the Jobs page after reboot
            if not self.selected_nodes:
                return redirect(url_for('servers', node=self.node, opt='getreports', project=self.project,
                                        spider=self.spider, version_job=self.job))

        # Click reports memu for the first time
        if not any([self.project, self.spider, self.job]):
            url_servers = ''
        else:
            url_servers = url_for('servers', node=self.node, opt='getreports', project=self.project,
                                  spider=self.spider, version_job=self.job)

        kwargs = dict(
            node=self.node,
            project=self.project,
            spider=self.spider,
            job=self.job,
            selected_nodes=self.selected_nodes,
            url_report=url_for('log', node=self.node, opt='report', project=self.project,
                               spider=self.spider, job=self.job),
            url_servers=url_servers,
            url_jobs=url_for('jobs', node=self.node),
            # url_nodereports=url_for('nodereports', node=self.node),
        )
        return render_template(self.template, **kwargs)
