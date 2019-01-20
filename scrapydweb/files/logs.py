# coding: utf8
import re

from flask import render_template, url_for

from ..myview import MyView
from ..vars import DIRECTORY_KEYS, DIRECTORY_PATTERN


class LogsView(MyView):
    methods = ['GET']

    def __init__(self):
        super(self.__class__, self).__init__()

        self.project = self.view_args['project']
        self.spider = self.view_args['spider']

        self.url = 'http://{}/logs/{}{}'.format(self.SCRAPYD_SERVER,
                                                '%s/' % self.project if self.project else '',
                                                '%s/' % self.spider if self.spider else '')
        self.template = 'scrapydweb/logs.html'
        self.text = ''

    def dispatch_request(self, **kwargs):
        status_code, self.text = self.make_request(self.url, auth=self.AUTH, api=False)
        if status_code != 200 or not re.search(r'Directory listing for /logs/', self.text):
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
        rows = [dict(zip(DIRECTORY_KEYS, row)) for row in re.findall(DIRECTORY_PATTERN, self.text)]
        for row in rows:
            # <a href="demo/">demo/</a>     dir
            # <a href="test/">test/</a>     dir
            # <a href="a.log">a.log</a>     file
            m = re.search(r'>(.*?)<', row['filename'])
            filename = m.group(1)
            if filename.endswith('/'):
                row['filename'] = re.sub(r'href=', 'class="link" href=', row['filename'])
            else:
                row['filename'] = u'<a class="link" target="_blank" href="{}">{}</a>'.format(
                                   self.url + filename, filename)
            if self.project and self.spider:
                row['url_log_stats'] = url_for('log', node=self.node, opt='stats',
                                               project=self.project, spider=self.spider,
                                               job=filename, with_ext='True')
                if filename.endswith('.json'):  # stats by LogParser
                    row['url_log_utf8'] = ''
                else:
                    row['url_log_utf8'] = url_for('log', node=self.node, opt='utf8',
                                                  project=self.project, spider=self.spider,
                                                  job=filename, with_ext='True')
                row['url_start'] = url_for('schedule.schedule', node=self.node, project=self.project,
                                           version=self.DEFAULT_LATEST_VERSION, spider=self.spider)
                row['url_multinode_start'] = url_for('overview', node=self.node,
                                                     opt='schedule', project=self.project,
                                                     version_job=self.DEFAULT_LATEST_VERSION, spider=self.spider)
        kwargs = dict(
            node=self.node,
            project=self.project,
            spider=self.spider,
            url=self.url,
            rows=rows
        )
        return render_template(self.template, **kwargs)
