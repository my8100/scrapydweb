# coding: utf8
import os
import io
import glob
import time
from datetime import datetime
import re
import json

from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask import current_app as app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from .utils import slot, uncompress_to_tmpdir, search_scrapy_cfg_path, build_egg
from ..vars import DEPLOY_PATH, DEMO_PROJECTS_PATH, INFO
from ..utils import make_request, json_dumps


bp = Blueprint('deploy', __name__, url_prefix='/')


def prepare_data():
    project_original = request.form.get('project', '') # Used with SCRAPY_PROJECTS_DIR
    project = re.sub(r'[^0-9A-Za-z_-]', '', project_original) or time.strftime('%Y-%m-%dT%H_%M_%S')
    version = re.sub(r'[^0-9A-Za-z_-]', '', request.form.get('version', '')) or time.strftime('%Y-%m-%dT%H_%M_%S')

    if request.files:
        # http://flask.pocoo.org/docs/1.0/api/#flask.Request.form
        # <class 'werkzeug.datastructures.FileStorage'>
        file = request.files['file']

        # Non-ASCII would be omitted and may set the eggname as to 'egg'
        filename = secure_filename(file.filename)
        if filename in ['egg', 'zip', 'tar', 'tar.gz']:
            filename = '%s_%s.%s' % (project, version, filename)
        else:
            filename = '%s_%s_from_file_%s' % (project, version, filename)

        if filename.endswith('egg'):
            eggname = filename
            eggpath = os.path.join(DEPLOY_PATH, eggname)
            file.save(eggpath)
        else: # Compressed file
            filepath = os.path.join(DEPLOY_PATH, filename)
            file.save(filepath)
            tmpdir = uncompress_to_tmpdir(filepath)

            # Search from the root of tmpdir
            (scrapy_cfg_path, paths) = search_scrapy_cfg_path(tmpdir)
            if not scrapy_cfg_path:
                return paths

            eggname = re.sub(r'(\.zip|\.tar|\.tar\.gz)$', '.egg', filename)
            eggpath = os.path.join(DEPLOY_PATH, eggname)
            build_egg(scrapy_cfg_path, eggname, eggpath)
    else:
        SCRAPY_PROJECTS_DIR = app.config.get('SCRAPY_PROJECTS_DIR', '') or DEMO_PROJECTS_PATH
        project_path = os.path.join(SCRAPY_PROJECTS_DIR, project_original) # Use project_original but not project

        (scrapy_cfg_path, paths) = search_scrapy_cfg_path(project_path)
        if not scrapy_cfg_path:
            return paths

        eggname = '%s_%s.egg' % (project, version)
        eggpath = os.path.join(DEPLOY_PATH, eggname)
        build_egg(scrapy_cfg_path, eggname, eggpath)

    with io.open(eggpath, 'rb') as f:
        content = f.read()
        data = {
            'project': project,
            'version': version,
            # 'egg': file.read()
            'egg': content
        }

    slot.add_egg(eggname, content)

    return eggname, project, version, data


@bp.route('/<int:node>/deploy/', methods=('GET', 'POST'))
def deploy(node):
    # return render_template('scrapydweb/hello.html')
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

    SCRAPY_PROJECTS_DIR = app.config.get('SCRAPY_PROJECTS_DIR', '') or DEMO_PROJECTS_PATH
    if SCRAPY_PROJECTS_DIR:
        scrapy_cfg_list = glob.glob(os.path.join(SCRAPY_PROJECTS_DIR, u'*/scrapy.cfg')) # python2 'ascii' codec can't decode byte
        projects_list = [os.path.dirname(i) for i in scrapy_cfg_list]
        projects = [os.path.basename(i) for i in projects_list]
        modification_times = [datetime.fromtimestamp(os.path.getmtime(i)).strftime('%Y-%m-%dT%H_%M_%S')
                              for i in projects_list]
    else:
        flash("Run ScrapydWeb with argument '--scrapy_projects_dir SCRAPY_PROJECTS_DIR' to enable auto eggifying.", INFO)
        projects = []
        modification_times = []

    return render_template('scrapydweb/deploy.html', node=node,
                           url=url_auth, selected_nodes=selected_nodes,
                           projects=projects, modification_times=modification_times,
                           SCRAPY_PROJECTS_DIR=SCRAPY_PROJECTS_DIR)


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

    ret = prepare_data()
    if isinstance(ret, list):
        alert = "Fail to deploy"
        text = "scrapy.cfg NOT found"
        return render_template('scrapydweb/result.html', node=node,
                               alert=alert, text=text, message=json_dumps(ret))
    else:
        eggname, project, version, data = ret

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
                                   eggname=eggname, project=project, version=version)
        else:
            return redirect(url_for('schedule.schedule', node=node,
                                    project=project, version=version,
                                    first_selected_node=first_selected_node if selected_nodes_amount else None))


@bp.route('/<int:node>/deploy/xhr/<eggname>/<project>/<version>/', methods=('POST', 'GET'))
def deploy_xhr(node, eggname, project, version):
    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])

    url = 'http://{}/{}.json'.format(SCRAPYD_SERVERS[node - 1], 'addversion')

    content = slot.egg.get(eggname)
    if not content:
        eggpath = os.path.join(DEPLOY_PATH, eggname)
        with io.open(eggpath, 'rb') as f:
            content = f.read()

    data = {
        'project': project,
        'version': version,
        'egg': content
    }
    status_code, js = make_request(url, data, auth=SCRAPYD_SERVERS_AUTHS[node - 1])
    return json_dumps(js)
