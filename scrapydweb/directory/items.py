# coding: utf8
import re

from flask import render_template

from ..myview import MyView
from ..vars import pattern_directory, keys_directory


class ItemsView(MyView):
    methods = ['GET']

    def __init__(self):
        super(self.__class__, self).__init__()

        self.project = self.view_args['project']
        self.spider = self.view_args['spider']

        self.url = 'http://{}/items/{}{}'.format(self.SCRAPYD_SERVER,
                                                 '%s/' % self.project if self.project else '',
                                                 '%s/' % self.spider if self.spider else '')
        self.template = 'scrapydweb/simpleui/items.html' if self.IS_SIMPLEUI else 'scrapydweb/items.html'

        self.text = ''

    def dispatch_request(self, **kwargs):
        status_code, self.text = self.make_request(self.url, api=False, auth=self.AUTH)
        if status_code != 200 or not re.search(r'Directory listing for /items/', self.text):
            kwargs = dict(
                node=self.node,
                url=self.url,
                status_code=status_code,
                text=self.text,
                message='Check out https://scrapyd.readthedocs.io/en/latest/config.html#items-dir for help'
            )
            return render_template(self.template_result, **kwargs)

        return self.generate_response()

    def generate_response(self):
        rows = [dict(zip(keys_directory, row)) for row in pattern_directory.findall(self.text)]

        for row in rows:
            # <a href="demo/">demo/</a>
            # <a href="test/">test/</a>
            # <a href="2018-10-09_225255.jl">2018-10-09_225255.jl</a>
            if self.project and self.spider:
                m = re.search(r'>(.*?)<', row['filename'])
                filename = m.group(1)
                row['filename'] = u'<a class="link" target="_blank" href="{}">{}</a>'.format(
                                   self.url + filename, filename)
            else:
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
