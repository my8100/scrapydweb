# coding: utf8
import re
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

from flask import flash, render_template, url_for

from ..myview import MyView
from ..vars import pageview_dict


JOB_PATTERN = re.compile(r"""
                            <tr>
                                <td>(?P<Project>.*?)</td>
                                <td>(?P<Spider>.*?)</td>
                                <td>(?P<Job>.*?)</td>
                                (?:<td>(?P<PID>.*?)</td>)?
                                (?:<td>(?P<Start>.*?)</td>)?
                                (?:<td>(?P<Runtime>.*?)</td>)?
                                (?:<td>(?P<Finish>.*?)</td>)?
                                (?:<td>(?P<Log>.*?)</td>)?
                                (?:<td>(?P<Items>.*?)</td>)?
                            </tr>
                          """, re.X)
JOB_KEYS = ['project', 'spider', 'job', 'pid', 'start', 'runtime', 'finish', 'log', 'items']


class DashboardView(MyView):
    methods = ['GET']
    pageview_dict = pageview_dict

    def __init__(self):
        super(self.__class__, self).__init__()

        self.url = 'http://%s/jobs' % self.SCRAPYD_SERVER
        self.template = 'scrapydweb/dashboard_mobileui.html' if self.USE_MOBILEUI else 'scrapydweb/dashboard.html'
        self.text = ''

    def dispatch_request(self, **kwargs):
        self.pageview_dict['dashboard'] += 1
        self.logger.info('pageview_dict: %s', self.pageview_dict)

        status_code, self.text = self.make_request(self.url, auth=self.AUTH, api=False)

        if status_code != 200 or not re.search(r'Jobs', self.text):
            kwargs = dict(
                node=self.node,
                url=self.url,
                status_code=status_code,
                text=self.text,
                tip='Click the above link to make sure your Scrapyd server is accessable.'
            )
            return render_template(self.template_fail, **kwargs)

        return self.generate_response()

    def generate_response(self):
        if self.SCRAPYD_SERVERS_AMOUNT > 1 and self.pageview_dict['dashboard'] == 1:
            flash("Use the navigation buttons above to quick scan the same page of neighbouring node", self.INFO)
        if not self.ENABLE_AUTH and self.SCRAPYD_SERVERS_AMOUNT == 1:
            flash("Set 'ENABLE_AUTH = True' to enable basic auth for web UI", self.INFO)
        if not self.SCRAPYD_LOGS_DIR and self.SCRAPYD_SERVER.split(':')[0] in ['127.0.0.1', 'localhost']:
            flash("Set up the 'SCRAPYD_LOGS_DIR' item to speed up loading scrapy logs.", self.INFO)
        if not self.ENABLE_LOGPARSER:
            flash("Set 'ENABLE_LOGPARSER  = True' to run LogParser as a subprocess at startup", self.WARN)
        if not self.ENABLE_EMAIL and self.SCRAPYD_SERVERS_AMOUNT == 1:
            flash("Set 'ENABLE_EMAIL = True' to enable email notice", self.INFO)

        rows = [dict(zip(JOB_KEYS, row)) for row in re.findall(JOB_PATTERN, self.text)]
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
                                                   version_job=self.DEFAULT_LATEST_VERSION, spider=row['spider'])
                row['url_schedule'] = url_for('schedule.schedule', node=self.node, project=row['project'],
                                              version=self.DEFAULT_LATEST_VERSION, spider=row['spider'])
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

        if self.DASHBOARD_FINISHED_JOBS_LIMIT > 0:
            finished_rows = finished_rows[::-1][:self.DASHBOARD_FINISHED_JOBS_LIMIT]
        else:
            finished_rows = finished_rows[::-1]
        kwargs = dict(
            node=self.node,
            colspan=14,
            url=self.url,
            url_liststats=url_for('api', node=self.node, opt='liststats'),
            url_liststats_source='http://%s/logs/stats.json' % self.SCRAPYD_SERVER,
            pending_rows=pending_rows,
            running_rows=running_rows,
            finished_rows=finished_rows,
            SHOW_DASHBOARD_JOB_COLUMN=self.SHOW_DASHBOARD_JOB_COLUMN,
            DASHBOARD_RELOAD_INTERVAL=self.DASHBOARD_RELOAD_INTERVAL,
            IS_IE_EDGE=self.IS_IE_EDGE,
            pageview=self.pageview_dict['dashboard'],
            FEATURES=self.FEATURES
        )
        return render_template(self.template, **kwargs)
