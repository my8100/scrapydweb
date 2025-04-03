# coding: utf-8
from flask import render_template, url_for

from ..baseview import BaseView


class MultinodeView(BaseView):
    methods = ['POST']

    def __init__(self):
        super(MultinodeView, self).__init__()

        self.opt = self.view_args['opt']
        self.project = self.view_args['project']
        self.version_job = self.view_args['version_job']

        self.template = 'scrapydweb/multinode_results.html'

    def dispatch_request(self, **kwargs):
        selected_nodes = self.get_selected_nodes()
        url_xhr = url_for('api', node=selected_nodes[0], opt=self.opt,
                          project=self.project, version_spider_job=self.version_job)

        if self.opt == 'stop':
            title = "Stop Job (%s) of Project (%s)" % (self.project, self.version_job)
            url_servers = url_for('servers', node=self.node, opt='listjobs', project=self.project)
            btn_servers = "Servers &raquo; List Running Jobs"
        elif self.opt == 'delversion':
            title = "Delete Version (%s) of Project (%s)" % (self.version_job, self.project)
            url_servers = url_for('servers', node=self.node, opt='listversions', project=self.project)
            btn_servers = "Servers &raquo; List Versions"
        else:  # elif opt == 'delproject':
            title = "Delete Project (%s)" % self.project
            url_servers = url_for('servers', node=self.node, opt='listprojects', project=self.project)
            btn_servers = "Servers &raquo; List Projects"

        kwargs = dict(
            node=self.node,
            title=title,
            opt=self.opt,
            project=self.project,
            version_job=self.version_job,
            selected_nodes=selected_nodes,
            url_xhr=url_xhr,
            url_servers=url_servers,
            btn_servers=btn_servers,
            url_projects_list=[url_for('projects', node=n) for n in range(1, self.SCRAPYD_SERVERS_AMOUNT + 1)]
        )
        return render_template(self.template, **kwargs)
