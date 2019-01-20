# coding: utf8
from collections import OrderedDict
import io
import os
import pickle
import re

from flask import Blueprint, redirect, render_template, request, send_from_directory, url_for

from ..myview import MyView
from ..vars import SCHEDULE_PATH
from .utils import slot


HISTORY_LOG = os.path.join(SCHEDULE_PATH, 'history.log')

UA_DICT = {
    'chrome': ("Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"),
    'iOS': ("Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) "
            "AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1"),
    'iPad': ("Mozilla/5.0 (iPad; CPU OS 9_1 like Mac OS X) "
             "AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1"),
    'Android': ("Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Mobile Safari/537.36")
}


def generate_cmd(auth, url, data):
    if auth:
        cmd = 'curl -u %s:%s %s' % (auth[0], auth[1], url)
    else:
        cmd = 'curl %s' % url

    for key, value in data.items():
        if key == 'setting':
            for v in value:
                if re.match(r'USER_AGENT=', v):
                    cmd += ' --data-urlencode "setting=%s=%s"' % (tuple(v.split('=', 1)))
                else:
                    cmd += ' -d setting=%s=%s' % (tuple(v.split('=', 1)))
        else:
            cmd += ' -d %s=%s' % (key, value)

    return cmd


def new_history_log():
    if not os.path.exists(HISTORY_LOG):
        with io.open(HISTORY_LOG, 'w', encoding='utf-8') as f:
            f.write('#' * 50 + u'\nhistory.log')


new_history_log()


bp = Blueprint('schedule', __name__, url_prefix='/')


@bp.route('/schedule/<filename>')
def history(filename):
    new_history_log()
    return send_from_directory(SCHEDULE_PATH, filename, mimetype='text/plain')


class ScheduleView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.project = self.view_args['project']
        self.version = self.view_args['version']
        self.spider = self.view_args['spider']

        self.url = 'http://%s/schedule.json' % self.SCRAPYD_SERVER
        self.template = 'scrapydweb/schedule.html'

    def dispatch_request(self, **kwargs):
        if self.POST:
            selected_nodes = self.get_selected_nodes()
            first_selected_node = selected_nodes[0]
        else:
            if self.project:
                # START button of Dashboard page / Run Spider button of Logs page
                selected_nodes = [self.node]
            else:
                selected_nodes = []
            first_selected_node = self.node

        kwargs = dict(
            node=self.node,
            project=self.project,
            version=self.version,
            spider=self.spider,
            # jobid=self.get_now_string(),
            url=self.url,
            selected_nodes=selected_nodes,
            first_selected_node=first_selected_node,
            url_overview=url_for('overview', node=self.node, opt='schedule'),
            url_schedule_run=url_for('schedule.run', node=self.node),
            url_schedule_history=url_for('schedule.history', filename='history.log'),
            url_listprojects=url_for('api', node=self.node, opt='listprojects'),
            url_listversions=url_for('api', node=self.node, opt='listversions', project='PROJECT_PLACEHOLDER'),
            url_listspiders=url_for('api', node=self.node, opt='listspiders', project='PROJECT_PLACEHOLDER',
                                    version_spider_job='VERSION_PLACEHOLDER'),
            url_schedule_check=url_for('schedule.check', node=self.node)
        )

        return render_template(self.template, **kwargs)


class CheckView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.url = 'http://%s/schedule.json' % self.SCRAPYD_SERVER
        self.template = 'scrapydweb/schedule.html'

        self.filename = ''
        self.data = OrderedDict()
        self.slot = slot

    def dispatch_request(self, **kwargs):
        self.prepare_data()
        self.logger.debug(self.data)

        cmd = generate_cmd(self.AUTH, self.url, self.data)
        # '-d' may be in project name, like 'ScrapydWeb-demo'
        cmd = re.sub(r'(curl -u\s+.*?:.*?)\s+(http://)', r'\1 \\\r\n\2', cmd)
        cmd = re.sub(r'\s+-d\s+', ' \\\r\n-d ', cmd)
        cmd = re.sub(r'\s+--data-urlencode\s+', ' \\\r\n--data-urlencode ', cmd)
        return self.json_dumps({'filename': self.filename, 'cmd': cmd})

    def prepare_data(self):
        for k, d in [('project', 'projectname'), ('_version', self.DEFAULT_LATEST_VERSION),
                     ('spider', 'spidername')]:
            self.data[k] = request.form.get(k, d)
        if self.data['_version'] == self.DEFAULT_LATEST_VERSION:
            self.data.pop('_version')

        self.data['jobid'] = re.sub(r'[^0-9A-Za-z_-]', '', request.form.get('jobid', '')) or self.get_now_string()

        self.data['setting'] = []
        ua = UA_DICT.get(request.form.get('USER_AGENT', ''), '')
        if ua:
            self.data['setting'].append('USER_AGENT=%s' % ua)

        for key in ['COOKIES_ENABLED', 'ROBOTSTXT_OBEY', 'CONCURRENT_REQUESTS', 'DOWNLOAD_DELAY']:
            value = request.form.get(key, '')
            if value:
                self.data['setting'].append("%s=%s" % (key, value))

        additional = request.form.get('additional', '').strip()
        if additional:
            parts = [i.strip() for i in re.split(r'-d\s+', re.sub(r'[\r\n]', ' ', additional)) if i.strip()]
            for part in parts:
                part = re.sub(r'\s*=\s*', '=', part)
                if '=' not in part:
                    continue
                m_setting = re.match(r'setting=([A-Z_]{6,31}=.+)', part)  # 'EDITOR' 'DOWNLOADER_CLIENTCONTEXTFACTORY'
                if m_setting:
                    self.data['setting'].append(m_setting.group(1))
                    continue
                m_arg = re.match(r'([a-zA-Z_][0-9a-zA-Z_]*)=(.+)', part)
                if m_arg and m_arg.group(1) != 'setting':
                    self.data[m_arg.group(1)] = m_arg.group(2)

        self.data['setting'].sort()
        _version = self.data.get('_version', 'default-the-latest-version')
        _filename = '{project}_{version}_{spider}'.format(project=self.data['project'],
                                                          version=_version,
                                                          spider=self.data['spider'])
        self.filename = '%s.pickle' % re.sub(r'[^0-9A-Za-z_-]', '', _filename)
        filepath = os.path.join(self.SCHEDULE_PATH, self.filename)
        with io.open(filepath, 'wb') as f:
            f.write(pickle.dumps(self.data))

        self.slot.add_data(self.filename, self.data)


class RunView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.url = ''
        self.template = 'scrapydweb/schedule_results.html'

        self.slot = slot
        self.selected_nodes_amount = 0
        self.selected_nodes = []
        self.first_selected_node = 0
        self.filename = request.form['filename']
        self.data = None
        self.js = {}

    def dispatch_request(self, **kwargs):
        self.handle_form()
        status_code, self.js = self.make_request(self.url, self.data, auth=self.AUTH)
        self.update_history()
        return self.generate_response()

    def handle_form(self):
        self.selected_nodes_amount = int(request.form.get('checked_amount', 0))
        # With multinodes, would try to Schedule to the first selected node first
        if self.selected_nodes_amount:
            self.selected_nodes = self.get_selected_nodes()
            self.first_selected_node = self.selected_nodes[0]
            self.url = 'http://%s/schedule.json' % self.SCRAPYD_SERVERS[self.first_selected_node - 1]
            # Note that self.first_selected_node != self.node
            self.AUTH = self.SCRAPYD_SERVERS_AUTHS[self.first_selected_node - 1]
        else:
            self.selected_nodes = [self.node]
            self.url = 'http://%s/schedule.json' % self.SCRAPYD_SERVER

        self.data = self.slot.data.get(self.filename)
        # self.data = None  # For test only
        if not self.data:
            filepath = os.path.join(self.SCHEDULE_PATH, self.filename)
            with io.open(filepath, 'rb') as f:
                self.data = pickle.loads(f.read())

    def update_history(self):
        new_history_log()
        with io.open(HISTORY_LOG, 'r+', encoding='utf-8') as f:
            content_backup = f.read()
            f.seek(0)
            content = os.linesep.join([
                '#' * 50,
                self.get_now_string(True),
                str([self.SCRAPYD_SERVERS[i - 1] for i in self.selected_nodes]),
                generate_cmd(self.AUTH, self.url, self.data),
                self.json_dumps(self.js),
                ''
            ])
            f.write(content)
            f.write(content_backup)

    def generate_response(self):
        if self.js['status'] == 'ok':
            if not self.selected_nodes_amount:
                return redirect(url_for('dashboard', node=self.node))

            kwargs = dict(
                node=self.node,
                project=self.data['project'],
                version=self.data.get('_version', self.DEFAULT_LATEST_VERSION),
                spider=self.data['spider'],
                selected_nodes=self.selected_nodes,
                first_selected_node=self.first_selected_node,
                js=self.js,
                url_dashboard_first_selected_node=url_for('dashboard', node=self.first_selected_node),
                url_xhr=url_for('schedule.schedule_xhr', node=self.node, filename=self.filename),
                url_overview=url_for('overview', node=self.node, opt='liststats', project=self.data['project'],
                                     version_job=self.js['jobid'])
            )
            return render_template(self.template, **kwargs)
        else:
            if self.selected_nodes_amount > 1:
                alert = ("Multinode schedule terminated, "
                         "since the first selected node returned status: " + self.js['status'])
            else:
                alert = "Fail to schedule, got status: " + self.js['status']

            message = self.js.get('message', '')
            if message:
                self.js['message'] = 'See details below'

            return render_template(self.template_fail, node=self.node,
                                   alert=alert, text=self.json_dumps(self.js), message=message)


class ScheduleXhrView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.filename = self.view_args['filename']

        self.url = 'http://%s/schedule.json' % self.SCRAPYD_SERVER

        self.slot = slot
        self.data = None

    def dispatch_request(self, **kwargs):
        self.data = self.slot.data.get(self.filename)
        # self.data = None  # For test only
        if not self.data:
            filepath = os.path.join(self.SCHEDULE_PATH, self.filename)
            with io.open(filepath, 'rb') as f:
                self.data = pickle.loads(f.read())

        status_code, js = self.make_request(self.url, self.data, auth=self.AUTH)
        return self.json_dumps(js)
