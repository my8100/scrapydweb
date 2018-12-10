# coding: utf8
import re
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from flask import render_template, flash, url_for

from ..myview import MyView
from ..vars import CHECK_UPDATE, INFO, WARN, pattern_jobs, keys_jobs, DEFAULT_LATEST_VERSION


page_view = 0 if CHECK_UPDATE else 1


class DashboardView(MyView):
    methods = ['GET']

    def __init__(self):
        super(self.__class__, self).__init__()

        self.url = 'http://%s/jobs' % self.SCRAPYD_SERVER
        self.template = 'scrapydweb/dashboard_mobileui.html' if self.IS_MOBILEUI else 'scrapydweb/dashboard.html'
        self.text = ''

        self.flag = ''
        if not self.IS_MOBILEUI and len(self.SCRAPYD_SERVERS) == 1:
            self.flag += 'A' if self.ENABLE_AUTH else '-'
            self.flag += 'C' if self.ENABLE_CACHE else '-'
            self.flag += 'E' if self.ENABLE_EMAIL else '-'

    def dispatch_request(self, **kwargs):
        global page_view
        page_view += 1

        status_code, self.text = self.make_request(self.url, api=False, auth=self.AUTH)

        if status_code != 200 or not re.search(r'Jobs', self.text):
            message = 'Click the above link to make sure your Scrapyd server is accessable'
            return render_template(self.template_fail, node=self.node,
                                   url=self.url, status_code=status_code,
                                   text=self.text, message=message)

        return self.generate_response()

    def generate_response(self):
        if self.IS_MOBILEUI:
            # flash("<a href='/'>Visit desktop version</a> to experience full features.", INFO)
            pass
        else:
            if len(self.SCRAPYD_SERVERS) > 1 and page_view == 1:
                flash("Use the navigation buttons above to quick scan the same page of neighbouring node", INFO)
            if not self.ENABLE_AUTH and len(self.SCRAPYD_SERVERS) == 1:
                flash("Set 'ENABLE_AUTH = True' to enable basic auth for web UI", INFO)
            if not self.SCRAPYD_LOGS_DIR and self.SCRAPYD_SERVER.split(':')[0] == '127.0.0.1':
                flash("Set up the 'SCRAPYD_LOGS_DIR' item to speed up loading scrapy logs.", INFO)
            if not self.ENABLE_CACHE:
                flash("Set 'ENABLE_CACHE = True' to enable caching HTML for Log and Stats page", WARN)
            if not self.ENABLE_EMAIL and len(self.SCRAPYD_SERVERS) == 1:
                flash("Set 'ENABLE_EMAIL = True' to enable email notice", WARN)

        rows = [dict(zip(keys_jobs, row)) for row in pattern_jobs.findall(self.text)]
        pending_rows = []
        running_rows = []
        finished_rows = []
        for row in rows:
            if not row['start']:
                pending_rows.append(row)
            else:
                job_finished = 'True' if row['finish'] else None
                row['url_utf8'] = url_for('log', node=self.node, opt='utf8', project=row['project'], ui=self.UI,
                                          spider=row['spider'], job=row['job'], job_finished=job_finished)
                row['url_stats'] = url_for('log', node=self.node, opt='stats', project=row['project'], ui=self.UI,
                                           spider=row['spider'], job=row['job'], job_finished=job_finished)
                row['url_multinode_stop'] = url_for('overview', node=self.node, opt='stop', project=row['project'],
                                                    version_job=row['job'])
                row['url_stop'] = url_for('api', node=self.node, opt='stop', project=row['project'],
                                          version_spider_job=row['job'])
                row['url_forcestop'] = url_for('api', node=self.node, opt='forcestop', project=row['project'],
                                               version_spider_job=row['job'])
                row['url_multinode_run'] = url_for('overview', node=self.node, opt='schedule', project=row['project'],
                                                   version_job=DEFAULT_LATEST_VERSION, spider=row['spider'])
                row['url_schedule'] = url_for('schedule.schedule', node=self.node, project=row['project'],
                                              version=DEFAULT_LATEST_VERSION, spider=row['spider'])
                row['url_start'] = url_for('api', node=self.node, opt='start', project=row['project'],
                                           version_spider_job=row['spider'])
                # <a href='/items/demo/test/2018-10-12_205507.jl'>Items</a>
                if row['items']:
                    _url_items = re.search(r"href='(.*?)'>", row['items']).group(1)
                    # row['url_items'] = re.sub(r'/jobs$', _url_items, self.url) + _url_items
                    row['url_items'] = urljoin(self.url, _url_items)

                if row['finish']:
                    finished_rows.append(row)
                else:
                    running_rows.append(row)

        kwargs = dict(
            node=self.node,
            colspan=12,
            url=self.url,
            scrapydweb_url='http://%s:%s' % (self.SCRAPYDWEB_BIND, self.SCRAPYDWEB_PORT),
            pending_rows=pending_rows,
            running_rows=running_rows,
            finished_rows=finished_rows,
            SHOW_DASHBOARD_JOB_COLUMN=self.SHOW_DASHBOARD_JOB_COLUMN,
            DASHBOARD_RELOAD_INTERVAL=self.DASHBOARD_RELOAD_INTERVAL,
            IS_IE_EDGE=self.IS_IE_EDGE,
            flag=self.flag,
            page_view=page_view
        )
        return render_template(self.template, **kwargs)
