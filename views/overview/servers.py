# coding: utf-8
from flask import flash, render_template, url_for

from ...common import handle_metadata
from ..baseview import BaseView


metadata = dict(pageview=handle_metadata().get('pageview', 1))


class ServersView(BaseView):
    metadata = metadata

    def __init__(self):
        super(ServersView, self).__init__()

        self.opt = self.view_args['opt']
        self.project = self.view_args['project']
        self.version_job = self.view_args['version_job']
        self.spider = self.view_args['spider']

        self.url = 'http://%s/daemonstatus.json' % self.SCRAPYD_SERVER
        self.template = 'scrapydweb/servers.html'
        self.selected_nodes = []

    def dispatch_request(self, **kwargs):
        self.metadata['pageview'] += 1
        self.logger.debug('metadata: %s', self.metadata)

        if self.SCRAPYD_SERVERS_AMOUNT > 1 and not (self.metadata['pageview'] > 2 and self.metadata['pageview'] % 100):
            if not self.ENABLE_AUTH:
                flash("Set 'ENABLE_AUTH = True' to enable basic auth for web UI", self.INFO)
            if self.IS_LOCAL_SCRAPYD_SERVER and not self.ENABLE_LOGPARSER:
                flash("Set 'ENABLE_LOGPARSER = True' to run LogParser as a subprocess at startup", self.WARN)
            if not self.ENABLE_MONITOR:
                flash("Set 'ENABLE_MONITOR = True' to enable the monitor feature", self.INFO)

        if self.POST:
            self.selected_nodes = self.get_selected_nodes()
        else:
            if self.SCRAPYD_SERVERS_AMOUNT == 1:
                self.selected_nodes = [1]
            else:
                self.selected_nodes = []

        kwargs = dict(
            node=self.node,
            opt=self.opt,
            project=self.project,
            version_job=self.version_job,
            spider=self.spider,
            url=self.url,
            selected_nodes=self.selected_nodes,
            IS_IE_EDGE=self.IS_IE_EDGE,
            pageview=self.metadata['pageview'],
            FEATURES=self.FEATURES,
            DEFAULT_LATEST_VERSION=self.DEFAULT_LATEST_VERSION,
            url_daemonstatus=url_for('api', node=self.node, opt='daemonstatus'),
            url_getreports=url_for('clusterreports', node=self.node, project='PROJECT_PLACEHOLDER',
                                   spider='SPIDER_PLACEHOLDER', job='JOB_PLACEHOLDER'),
            url_liststats=url_for('api', node=self.node, opt='liststats', project='PROJECT_PLACEHOLDER',
                                  version_spider_job='JOB_PLACEHOLDER'),
            url_listprojects=url_for('api', node=self.node, opt='listprojects'),
            url_listversions=url_for('api', node=self.node, opt='listversions', project='PROJECT_PLACEHOLDER'),
            url_listspiders=url_for('api', node=self.node, opt='listspiders', project='PROJECT_PLACEHOLDER',
                                    version_spider_job='VERSION_PLACEHOLDER'),
            url_listjobs=url_for('api', node=self.node, opt='listjobs', project='PROJECT_PLACEHOLDER'),
            url_deploy=url_for('deploy', node=self.node),
            url_schedule=url_for('schedule', node=self.node, project='PROJECT_PLACEHOLDER',
                                 version='VERSION_PLACEHOLDER', spider='SPIDER_PLACEHOLDER'),
            url_stop=url_for('multinode', node=self.node, opt='stop', project='PROJECT_PLACEHOLDER',
                             version_job='JOB_PLACEHOLDER'),
            url_delversion=url_for('multinode', node=self.node, opt='delversion', project='PROJECT_PLACEHOLDER',
                                   version_job='VERSION_PLACEHOLDER'),
            url_delproject=url_for('multinode', node=self.node, opt='delproject', project='PROJECT_PLACEHOLDER')
        )
        return render_template(self.template, **kwargs)
