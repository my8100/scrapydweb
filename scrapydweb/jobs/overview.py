# coding: utf8
from flask import render_template, flash

from ..myview import MyView
from ..vars import INFO, WARN


page_view = 0


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

        if len(self.SCRAPYD_SERVERS) == 1:
            flash("Run ScrapydWeb with argument '-ss 127.0.0.1 -ss username:password@192.168.123.123:6801#group' "
                  "to set up any number of Scrapyd servers to control.", INFO)
        else:
            if not self.AUTH_ENABLED:
                flash("Set 'DISABLE_AUTH = False' to enable basic auth for web UI", INFO)
            if not self.CACHE_ENABLED:
                flash("Set 'DISABLE_CACHE = False' to enable caching HTML for Log and Stats page", WARN)
            if not self.EMAIL_ENABLED:
                flash("Set 'DISABLE_EMAIL = False' to enable email notice", WARN)

        if self.POST:
            self.selected_nodes = self.get_selected_nodes()
        else:
            if len(self.SCRAPYD_SERVERS) == 1:
                self.selected_nodes = [1]
            else:
                self.selected_nodes = []

        if self.EMAIL_ENABLED:
            flag = 'E'
        elif self.AUTH_ENABLED:
            flag = 'A'
        elif self.CACHE_ENABLED:
            flag = 'C'
        else:
            flag = 'X'
            
        kwargs = dict(
            node=self.node,
            opt=self.opt,
            project=self.project,
            version_job=self.version_job,
            spider=self.spider,
            url=self.url,
            selected_nodes=self.selected_nodes,
            page_view=page_view,
            flag=flag
        )
        return render_template(self.template, **kwargs)
