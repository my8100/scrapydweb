# coding: utf8
import re
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from flask import render_template, flash

from ..myview import MyView
from ..vars import INFO, WARN, pattern_jobs, keys_jobs


page_view = 0


class DashboardView(MyView):
    methods = ['GET']

    def __init__(self):
        super(self.__class__, self).__init__()

        self.url = 'http://%s/jobs' % self.SCRAPYD_SERVER
        self.template = 'scrapydweb/simpleui/index.html' if self.IS_SIMPLEUI else 'scrapydweb/dashboard.html'
        self.text = ''

    def dispatch_request(self, **kwargs):
        global page_view
        page_view += 1

        status_code, self.text = self.make_request(self.url, api=False, auth=self.AUTH)

        if status_code != 200 or not re.search(r'Jobs', self.text):
            return render_template(self.template_result, node=self.node,
                                   url=self.url, status_code=status_code, text=self.text)

        return self.generate_response()

    def generate_response(self):
        if self.IS_SIMPLEUI:
            flash("<a href='/'>Visit desktop version</a> to experience full features.", INFO)
        else:
            if len(self.SCRAPYD_SERVERS) > 1 and page_view == 1:
                flash("Use the navigation buttons above to fast switch to the same page of neighbouring node", INFO)
            if not self.AUTH_ENABLED and len(self.SCRAPYD_SERVERS) == 1:
                flash("Set 'DISABLE_AUTH = False' to enable basic auth for web UI", INFO)
            if not self.SCRAPYD_LOGS_DIR and self.SCRAPYD_SERVER.split(':')[0] == '127.0.0.1':
                flash("Set up the item 'SCRAPYD_LOGS_DIR' to speed up loading scrapy logs.", INFO)
            if not self.CACHE_ENABLED:
                flash("Set 'DISABLE_CACHE = False' to enable caching HTML for Log and Stats page", WARN)
            if not self.EMAIL_ENABLED and len(self.SCRAPYD_SERVERS) == 1:
                flash("Set 'DISABLE_EMAIL = False' to enable email notice", WARN)

        rows = [dict(zip(keys_jobs, row)) for row in pattern_jobs.findall(self.text)]
        pending_rows = []
        running_rows = []
        finished_rows = []
        for row in rows:
            # <a href='/items/demo/test/2018-10-12_205507.jl'>Items</a>
            if row['items']:
                _url_items = re.search(r"href='(.*?)'>", row['items']).group(1)
                # row['url_items'] = re.sub(r'/jobs$', _url_items, self.url) + _url_items
                row['url_items'] = urljoin(self.url, _url_items)

            if not row['start']:
                pending_rows.append(row)
            elif not row['finish']:
                running_rows.append(row)
            else:
                finished_rows.append(row)

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
            colspan=12,
            ui=self.UI,
            url=self.url,
            scrapydweb_url='http://%s:%s' % (self.SCRAPYDWEB_BIND, self.SCRAPYDWEB_PORT),
            pending_rows=pending_rows,
            running_rows=running_rows,
            finished_rows=finished_rows,
            SHOW_DASHBOARD_JOB_COLUMN=self.SHOW_DASHBOARD_JOB_COLUMN,
            DASHBOARD_RELOAD_INTERVAL=self.DASHBOARD_RELOAD_INTERVAL,
            page_view=page_view,
            flag=flag
        )
        return render_template(self.template, **kwargs)
