# coding: utf8
import os
import io
import time
import re
import json
from collections import OrderedDict
import pickle

from flask import Blueprint, render_template, request, url_for, send_from_directory, redirect
from flask import current_app as app

from .utils import slot
from ..vars import SCHEDULE_PATH, DEFAULT_LATEST_VERSION, UA_DICT
from ..utils import make_request, json_dumps

HISTORY_LOG = os.path.join(SCHEDULE_PATH, 'history.log')
if not os.path.exists(HISTORY_LOG):
    with io.open(HISTORY_LOG, 'w') as f:
        f.write(u'history.log')

bp = Blueprint('schedule', __name__, url_prefix='/')


def prepare_data():
    data = OrderedDict()
    for k, d in [('project', 'projectname'), ('_version', DEFAULT_LATEST_VERSION),
                 ('spider', 'spidername')]:
        data[k] = request.form.get(k, d)
    if data['_version'] == DEFAULT_LATEST_VERSION:
        data.pop('_version')

    data['jobid'] = re.sub(r'[^0-9A-Za-z_-]', '', request.form.get('jobid', '')) or time.strftime('%Y-%m-%d_%H%M%S')

    data['setting'] = []
    ua = UA_DICT.get(request.form.get('USER_AGENT', ''), '')
    if ua:
        data['setting'].append('USER_AGENT="%s"' % ua)

    for key in ['ROBOTSTXT_OBEY', 'CONCURRENT_REQUESTS', 'DOWNLOAD_DELAY']:
        value = request.form.get(key, '')
        if value:
            data['setting'].append("%s=%s" % (key, value))

    additional = request.form.get('additional', '').strip()
    if additional:
        parts = [i.strip() for i in re.split('-d\s+', re.sub(r'\r|\n', ' ', additional)) if i.strip()]
        for part in parts:
            part = re.sub(r'\s*=\s*', '=', part)
            if '=' not in part:
                continue
            m_setting = re.match(r'setting=([A-Z_]{6,31}=.+)', part)  # 'EDITOR' 'DOWNLOADER_CLIENTCONTEXTFACTORY'
            if m_setting:
                data['setting'].append(m_setting.group(1))
                continue
            m_arg = re.match(r'([a-zA-Z_][0-9a-zA-Z_]*)=(.+)', part)
            if m_arg and m_arg.group(1) != 'setting':
                data[m_arg.group(1)] = m_arg.group(2)

    filename = '%s_%s_%s' % (data['project'], data.get('_version', 'default-the-latest-version'), data['spider'])
    filename = '%s.pickle' % re.sub(r'[^0-9A-Za-z_-]', '', filename)
    filepath = os.path.join(SCHEDULE_PATH, filename)
    with io.open(filepath, 'wb') as f:
        f.write(pickle.dumps(data))

    slot.add_data(filename, data)

    return filename, data


def generate_cmd(url, data):
    cmd = 'curl %s' % url
    for key, value in data.items():
        if key == 'setting':
            for v in value:
                # print(value)
                cmd += ' -d setting=%s=%s' % (tuple(v.split('=', 1)))
        else:
            cmd += ' -d %s=%s' % (key, value)
    return cmd


@bp.route('/<int:node>/schedule/<project>/<version>/<spider>/', methods=('POST', 'GET'))
@bp.route('/<int:node>/schedule/<project>/<version>/', methods=('POST', 'GET'))
@bp.route('/<int:node>/schedule/<project>/', methods=('POST', 'GET'))  # For /overview/
@bp.route('/<int:node>/schedule/', methods=('POST', 'GET'))
def schedule(node, project=None, version=None, spider=None):
    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])

    # $ curl http://localhost:6800/schedule.json -d project=myproject -d spider=somespider
    url = 'http://%s/schedule.json' % SCRAPYD_SERVERS[node - 1]
    auth = SCRAPYD_SERVERS_AUTHS[node - 1]
    url_auth = url.replace('http://', 'http://%s:%s@' % auth) if auth else url

    if request.method == 'POST':
        selected_nodes = []
        for i in range(1, len(SCRAPYD_SERVERS) + 1):
            if request.form.get(str(i)) == 'on':
                selected_nodes.append(i)
        first_selected_node = selected_nodes[0]
    else:
        # RUN SPIDER button of DEPLOY PROJECT results(keep home url)
        # first_selected_node = request.args.get('first_selected_node', None)
        # if first_selected_node:
        # first_selected_node = int(first_selected_node)
        # else:
        # first_selected_node = node
        # selected_nodes = [first_selected_node]

        first_selected_node = node
        if project:
            # START button of Dashboard or Logs page, RUN SPIDER button of DEPLOY PROJECT results(change home url)
            selected_nodes = [node]
        else:
            selected_nodes = []

    return render_template('scrapydweb/schedule.html', node=node,
                           url=url_auth, project=project, version=version, spider=spider,
                           jobid=time.strftime('%Y-%m-%d_%H%M%S'),
                           selected_nodes=selected_nodes, first_selected_node=first_selected_node)


@bp.route('/<int:node>/schedule/check/', methods=('POST', 'GET'))
def check(node):
    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])

    url = 'http://%s/schedule.json' % SCRAPYD_SERVERS[node - 1]

    filename, data = prepare_data()
    app.logger.debug(data)

    cmd = generate_cmd(url, data)

    return json.dumps({'filename': filename, 'cmd': re.sub(r'-d', '\r\n-d', cmd)})


@bp.route('/<int:node>/schedule/run/', methods=('POST', 'GET'))
def run(node):
    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])

    selected_nodes_amount = request.form.get('checked_amount', None)
    # Schedule to the first selected node
    if selected_nodes_amount:
        selected_nodes = []
        for i in range(1, len(SCRAPYD_SERVERS) + 1):
            if request.form.get(str(i)) == 'on':
                selected_nodes.append(i)
        first_selected_node = selected_nodes[0]
        url = 'http://%s/schedule.json' % SCRAPYD_SERVERS[first_selected_node - 1]
    else:
        selected_nodes = [node]
        url = 'http://%s/schedule.json' % SCRAPYD_SERVERS[node - 1]

    filename = request.form['filename']
    data = slot.data.get(filename)
    if not data:
        filepath = os.path.join(SCHEDULE_PATH, filename)
        with io.open(filepath, 'rb') as f:
            data = pickle.loads(f.read())

    status_code, js = make_request(url, data, auth=SCRAPYD_SERVERS_AUTHS[node - 1])

    with io.open(HISTORY_LOG, 'r+', encoding='utf8') as f:
        history = f.read()
        f.seek(0)
        f.write(os.linesep.join([
            '#' * 50,
            time.ctime(),
            str([SCRAPYD_SERVERS[i - 1] for i in selected_nodes]),
            generate_cmd(url, data),
            json_dumps(js),
            ''
        ]))
        f.write(history)

    if js['status'] == 'ok':
        if selected_nodes_amount:
            project = data['project']
            version = data.get('_version', DEFAULT_LATEST_VERSION)
            spider = data['spider']
            return render_template('scrapydweb/schedule_results.html', node=node,
                                   selected_nodes=selected_nodes,
                                   first_selected_node=first_selected_node, js=js,
                                   filename=filename, project=project, version=version, spider=spider)
        else:
            return redirect(url_for('dashboard.dashboard', node=node))
    else:
        message = js.get('message', '')
        if message:
            js.update({'message': 'See below'})
        js['info'] = "Maybe the project egg file had been deleted, check in the 'Projects > Manage' page."

        if selected_nodes_amount and int(selected_nodes_amount) > 1:
            alert = "Schedule terminated, since the first selected node returned status: " + js['status']
        else:
            alert = "Fail to schedule, got status: " + js['status']

        return render_template('scrapydweb/result.html', node=node,
                               text=json_dumps(js),
                               message=message, alert=alert)


@bp.route('/<int:node>/schedule/xhr/<filename>/', methods=('POST', 'GET'))
def schedule_xhr(node, filename):
    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])

    url = 'http://%s/schedule.json' % SCRAPYD_SERVERS[node - 1]

    data = slot.data.get(filename)
    if not data:
        filepath = os.path.join(SCHEDULE_PATH, filename)
        with io.open(filepath, 'rb') as f:
            data = pickle.loads(f.read())

    status_code, js = make_request(url, data, auth=SCRAPYD_SERVERS_AUTHS[node - 1])
    return json_dumps(js)


@bp.route('/schedule/<filename>')
def history(filename):
    return send_from_directory(SCHEDULE_PATH, filename, mimetype='text/plain')
