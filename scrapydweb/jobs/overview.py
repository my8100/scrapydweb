# coding: utf8
from flask import render_template, flash, url_for

from ..myview import MyView
from ..vars import CHECK_UPDATE, INFO, WARN


page_view = 0 if CHECK_UPDATE else 1


class OverviewView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.opt = self.view_args['opt']
        self.project = self.view_args['project']
        self.version_job = self.view_args['version_job']
        self.spider = self.view_args['spider']

        self.url = 'http://%s/daemonstatus.json' % self.SCRAPYD_SERVER
        self.template = 'scrapydweb/overview.html'
        self.selected_nodes = []

    def dispatch_request(self, **kwargs):
        global page_view
        page_view += 1

        if self.SCRAPYD_SERVERS_AMOUNT > 1:
            if not self.ENABLE_AUTH:
                flash("Set 'ENABLE_AUTH = True' to enable basic auth for web UI", INFO)
            if not self.ENABLE_CACHE:
                flash("Set 'ENABLE_CACHE = True' to enable caching HTML for Log and Stats page", WARN)
            if not self.ENABLE_EMAIL:
                flash("Set 'ENABLE_EMAIL = True' to enable email notice", INFO)

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
            page_view=page_view,
            FEATURES=self.FEATURES,
            url_daemonstatus=url_for('api', node=self.node, opt='daemonstatus'),
            url_listprojects=url_for('api', node=self.node, opt='listprojects'),
            url_listversions=url_for('api', node=self.node, opt='listversions', project='PROJECT_PLACEHOLDER'),
            url_listspiders=url_for('api', node=self.node, opt='listspiders', project='PROJECT_PLACEHOLDER',
                                    version_spider_job='VERSION_PLACEHOLDER'),
            url_listjobs=url_for('api', node=self.node, opt='listjobs', project='PROJECT_PLACEHOLDER'),
            url_deploy=url_for('deploy.deploy', node=self.node),
            url_schedule=url_for('schedule.schedule', node=self.node, project='PROJECT_PLACEHOLDER',
                                 version='VERSION_PLACEHOLDER', spider='SPIDER_PLACEHOLDER'),
            url_stop=url_for('multinode', node=self.node, opt='stop', project='PROJECT_PLACEHOLDER',
                             version_job='JOB_PLACEHOLDER'),
            url_delversion=url_for('multinode', node=self.node, opt='delversion', project='PROJECT_PLACEHOLDER',
                                   version_job='VERSION_PLACEHOLDER'),
            url_delproject=url_for('multinode', node=self.node, opt='delproject', project='PROJECT_PLACEHOLDER')
        )
        return render_template(self.template, **kwargs)
