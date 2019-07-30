# coding: utf-8
import os
import re

from flask import render_template, url_for

from ...vars import DIRECTORY_KEYS, DIRECTORY_PATTERN, HREF_NAME_PATTERN
from ..baseview import BaseView


class ItemsView(BaseView):
    methods = ['GET']

    def __init__(self):
        super(ItemsView, self).__init__()

        self.project = self.view_args['project']
        self.spider = self.view_args['spider']

        self.url = 'http://{}/items/{}{}'.format(self.SCRAPYD_SERVER,
                                                 '%s/' % self.project if self.project else '',
                                                 '%s/' % self.spider if self.spider else '')
        self.template = 'scrapydweb/items.html'
        self.text = ''

    def dispatch_request(self, **kwargs):
        status_code, self.text = self.make_request(self.url, auth=self.AUTH, as_json=False)
        if status_code != 200 or not re.search(r'Directory listing for /items/', self.text):
            kwargs = dict(
                node=self.node,
                url=self.url,
                status_code=status_code,
                text=self.text,
                tip="Click the above link to make sure your Scrapyd server is accessable. "
            )
            return render_template(self.template_fail, **kwargs)

        return self.generate_response()

    def generate_response(self):
        rows = [dict(zip(DIRECTORY_KEYS, row)) for row in re.findall(DIRECTORY_PATTERN, self.text)]
        for row in rows:
            # <a href="demo/">demo/</a>     dir
            # <a href="test/">test/</a>     dir
            # <a href="a.jl">a.jl</a>       file
            row['href'], row['filename'] = re.search(HREF_NAME_PATTERN, row['filename']).groups()
            if not row['href'].endswith('/'):  # It's a file but not a directory
                row['href'] = self.url + row['href']

            if self.project and self.spider:
                if row['filename'].endswith('.tar.gz'):
                    filename_without_ext = row['filename'][:-len('.tar.gz')]
                else:
                    filename_without_ext = os.path.splitext(row['filename'])[0]  # '1.1.jl' => ('1.1', '.jl')
                row['url_stats'] = url_for('log', node=self.node, opt='stats', project=self.project,
                                           spider=self.spider, job=filename_without_ext)
                row['url_utf8'] = url_for('log', node=self.node, opt='utf8', project=self.project,
                                          spider=self.spider, job=filename_without_ext)
                row['url_clusterreports'] = url_for('clusterreports', node=self.node, project=self.project,
                                                    spider=self.spider, job=self.get_job_without_ext(row['filename']))
        if self.project and self.spider:
            url_schedule = url_for('schedule', node=self.node, project=self.project,
                                   version=self.DEFAULT_LATEST_VERSION, spider=self.spider)
            url_multinode_run = url_for('servers', node=self.node, opt='schedule', project=self.project,
                                        version_job=self.DEFAULT_LATEST_VERSION, spider=self.spider)
        else:
            url_schedule = url_multinode_run = ''
        kwargs = dict(
            node=self.node,
            project=self.project,
            spider=self.spider,
            url=self.url,
            url_schedule=url_schedule,
            url_multinode_run=url_multinode_run,
            rows=rows
        )
        return render_template(self.template, **kwargs)
