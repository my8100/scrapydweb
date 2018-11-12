# coding: utf8
import re

from flask import render_template, url_for

from ..myview import MyView
from ..vars import DEFAULT_LATEST_VERSION, pattern_directory, keys_directory


class LogsView(MyView):
    methods = ['GET']

    def __init__(self):
        super(self.__class__, self).__init__()

        self.project = self.view_args['project']
        self.spider = self.view_args['spider']

        self.url = 'http://{}/logs/{}{}'.format(self.SCRAPYD_SERVER,
                                                '%s/' % self.project if self.project else '',
                                                '%s/' % self.spider if self.spider else '')
        self.template = 'scrapydweb/simpleui/logs.html' if self.IS_SIMPLEUI else 'scrapydweb/logs.html'
        self.text = ''

    def dispatch_request(self, **kwargs):
        status_code, self.text = self.make_request(self.url, api=False, auth=self.AUTH)
        if status_code != 200 or not re.search(r'Directory listing for /logs/', self.text):
            kwargs = dict(
                node=self.node,
                url=self.url,
                status_code=status_code,
                text=self.text
            )
            return render_template(self.template_result, **kwargs)

        return self.generate_response()

    def generate_response(self):
        rows = [dict(zip(keys_directory, row)) for row in pattern_directory.findall(self.text)]

        for row in rows:
            if self.project and self.spider:
                # <a href="098726cca42b11e8a8b514dda9e91c2f.log">098726cca42b11e8a8b514dda9e91c2f.log</a>
                m = re.search(r'>(.*?)<', row['filename'])
                filename = m.group(1)
                row['filename'] = u'<a class="link" target="_blank" href="{}">{}</a>'.format(
                                   self.url + filename, filename)

                row['url_log_utf8'] = url_for('log', node=self.node, opt='utf8',
                                              project=self.project, spider=self.spider,
                                              job=filename, with_ext='True', ui=self.UI)
                row['url_log_stats'] = url_for('log', node=self.node, opt='stats',
                                               project=self.project, spider=self.spider,
                                               job=filename, with_ext='True', ui=self.UI)
                if self.IS_SIMPLEUI:
                    row['url_start'] = url_for('api', node=self.node, opt='start', project=self.project,
                                               version_spider_job=self.spider, ui=self.UI)
                else:
                    row['url_start'] = url_for('schedule.schedule', node=self.node, project=self.project,
                                               version=DEFAULT_LATEST_VERSION, spider=self.spider)
                    row['url_multinode_start'] = url_for('overview', node=self.node,
                                                         opt='schedule', project=self.project,
                                                         version_job=DEFAULT_LATEST_VERSION, spider=self.spider)
            else:
                # <a href="proxy/">proxy/</a>
                if self.IS_SIMPLEUI:
                    row['filename'] = re.sub(r'href="(.*?)"', r'href="\1?ui=simple"', row['filename'])
                else:
                    row['filename'] = re.sub(r'href=', 'class="link" href=', row['filename'])

        kwargs = dict(
            node=self.node,
            project=self.project,
            spider=self.spider,
            url=self.url,
            rows=rows
        )
        return render_template(self.template, **kwargs)
