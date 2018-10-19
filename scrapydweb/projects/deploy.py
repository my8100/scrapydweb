# coding: utf8
import os
import io
import time
import re
import json

from flask import Blueprint, render_template, request, url_for, redirect
from flask import current_app as app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from .utils import slot
from ..vars import DEPLOY_PATH
from ..utils import make_request, json_dumps

bp = Blueprint('deploy', __name__, url_prefix='/')


def prepare_data():
    # http://flask.pocoo.org/docs/1.0/api/#flask.Request.form
    # <class 'werkzeug.datastructures.FileStorage'>
    file = request.files['file']
    project = re.sub(r'[^0-9A-Za-z_-]', '', request.form['project']) or time.strftime('%Y-%m-%d_%H%M%S')
    version = re.sub(r'[^0-9A-Za-z_-]', '', request.form['version']) or time.strftime('%Y-%m-%d_%H%M%S')

    # Non-ASCII would be omitted and may result filename to 'egg'
    filename = secure_filename(file.filename)
    if filename == 'egg':
        filename = '%s_%s.egg' % (project, version)
    else:
        filename = '%s_%s_%s.egg' % (filename.rpartition('.')[0], project, version)
    filepath = os.path.join(DEPLOY_PATH, filename)
    file.save(filepath)

    with io.open(filepath, 'rb') as f:
        content = f.read()
        data = {
            'project': project,
            'version': version,
            # 'egg': file.read()
            'egg': content
        }

    slot.add_egg(filename, content)

    return filename, project, version, data


@bp.route('/<int:node>/deploy/', methods=('GET', 'POST'))
def deploy(node):
    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])

    # $ curl http://localhost:6800/addversion.json -F project=myproject -F version=r23 -F egg=@myproject.egg
    # {'node_name': 'win7-PC', 'status': 'ok', 'project': 'demo', 'version': '2018-09-05T03_13_50', 'spiders': 1}
    url = 'http://{}/{}.json'.format(SCRAPYD_SERVERS[node - 1], 'addversion')
    auth = SCRAPYD_SERVERS_AUTHS[node - 1]
    url_auth = url.replace('http://', 'http://%s:%s@' % auth) if auth else url

    if request.method == 'POST':
        selected_nodes = []
        for i in range(1, len(SCRAPYD_SERVERS) + 1):
            if request.form.get(str(i)) == 'on':
                selected_nodes.append(i)
    else:
        # first_selected_node = request.args.get('first_selected_node', None)
        # if first_selected_node:
        # selected_nodes = [int(first_selected_node)]
        # else:
        # selected_nodes = [node]
        selected_nodes = []

    return render_template('scrapydweb/deploy.html', node=node,
                           url=url_auth, selected_nodes=selected_nodes)


@bp.route('/<int:node>/deploy/upload/', methods=('POST',))
def upload(node):
    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])

    selected_nodes_amount = request.form.get('checked_amount', None)
    # Deploy to the first selected node
    if selected_nodes_amount:
        selected_nodes = []
        for i in range(1, len(SCRAPYD_SERVERS) + 1):
            if request.form.get(str(i)) == 'on':
                selected_nodes.append(i)
        first_selected_node = selected_nodes[0]
        url = 'http://{}/{}.json'.format(SCRAPYD_SERVERS[first_selected_node - 1], 'addversion')
    else:
        url = 'http://{}/{}.json'.format(SCRAPYD_SERVERS[node - 1], 'addversion')
    # {'1': 'on',
    # '2': 'on',
    # 'checked_amount': '2',
    # 'project': 'demo',
    # 'version': '2018-09-05T03_13_50'}
    filename, project, version, data = prepare_data()
    status_code, js = make_request(url, data, auth=SCRAPYD_SERVERS_AUTHS[node - 1])

    if js['status'] != 'ok':
        if selected_nodes_amount and int(selected_nodes_amount) > 1:
            alert = "Deployment terminated, since the first selected node returned status: " + js['status']
        else:
            alert = "Fail to deploy, got status: " + js['status']
        message = js.get('message', '')
        if message:
            js.update({'message': 'See below'})

        return render_template('scrapydweb/result.html', node=node,
                               text=json_dumps(js),
                               message=message, alert=alert)
    else:
        if selected_nodes_amount:  # and int(selected_nodes_amount) > 1:
            return render_template('scrapydweb/deploy_results.html', node=node,
                                   selected_nodes=selected_nodes,
                                   first_selected_node=first_selected_node, js=js,
                                   filename=filename, project=project, version=version)
        else:
            return redirect(url_for('schedule.schedule', node=node,
                                    project=project, version=version,
                                    first_selected_node=first_selected_node if selected_nodes_amount else None))


@bp.route('/<int:node>/deploy/xhr/<filename>/<project>/<version>/', methods=('POST', 'GET'))
def deploy_xhr(node, filename, project, version):
    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])

    url = 'http://{}/{}.json'.format(SCRAPYD_SERVERS[node - 1], 'addversion')

    content = slot.egg.get(filename)
    if not content:
        filepath = os.path.join(DEPLOY_PATH, filename)
        with io.open(filepath, 'rb') as f:
            content = f.read()

    data = {
        'project': project,
        'version': version,
        'egg': content
    }
    status_code, js = make_request(url, data, auth=SCRAPYD_SERVERS_AUTHS[node - 1])
    return json_dumps(js)
