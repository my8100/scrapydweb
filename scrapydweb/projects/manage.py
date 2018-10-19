# coding: utf8
import datetime
import json

from flask import Blueprint, render_template, request, url_for
from flask import current_app as app

from ..api import api
from ..utils import json_dumps

bp = Blueprint('manage', __name__, url_prefix='/')


@bp.route('/<int:node>/manage/<opt>/<project>/<version_spider_job>/', methods=('POST', 'GET'))  # GET for url_for ???
@bp.route('/<int:node>/manage/<opt>/<project>/', methods=('POST', 'GET'))
@bp.route('/<int:node>/manage/')  # /manage/ >>> listprojects
def manage(node, opt='listprojects', project=None, version_spider_job=None):
    text = api(node, opt, project, version_spider_job)
    js = json.loads(text)

    # "listversions" NOT included
    if js['status'] != 'ok' and opt in ['listprojects', 'listspiders', 'delversion', 'delproject']:
        if request.method == 'POST':
            # Pass request.url instead of js['url'], for GET method
            return ('<a class="link" target="_blank" href="%s">REQUEST</a>'
                    '<em style="color: red;"> got status: %s</em>') % (request.url, js['status'])
        else:
            message = js.get('message', '')
            if message:
                js.update({'message': 'See below'})
            return render_template('scrapydweb/result.html', node=node,
                                   text=json_dumps(js),
                                   message=message)


    if opt == 'listprojects':
        node_name = js['node_name']
        projects = js['projects']
        results = []
        for project in projects:
            url_listversions = url_for('.manage', node=node, opt='listversions', project=project)
            results.append((project, url_listversions))
        if request.method == 'POST':
            url = js['url']
        else:
            SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])
            auth = SCRAPYD_SERVERS_AUTHS[node - 1]
            url = js['url'].replace('http://', 'http://%s:%s@' % auth) if auth else js['url']
        return render_template('scrapydweb/manage.html', node=node,
                               url=url, node_name=node_name, results=results,
                               url_deploy=url_for('deploy.deploy', node=node))

    elif opt == 'listversions':
        if js['status'] != 'ok':
            return ('<a class="link" target="_blank" href="{url}">REQUEST</a>'
                    '<em style="color: red;"> got status: {status}</em>'
                    '<br>Click to <a class="link" href="{url_deploy}">DEPLOY the project</a> '
                    'with another project name or click to directly '
                    '<a class="link" style="color: red;" target="_blank" href="{url_delproject}">'
                    'DELETE current project</a>'
                    '<pre>{text}</pre>').format(
                url=js['url'], status=js['status'],
                url_delproject=url_for('manage.manage', node=node, opt='delproject', project=project),
                url_deploy=url_for('deploy.deploy', node=node), text=text)

        node_name = js['node_name']
        versions = js['versions']
        url_delproject = url_for('.manage', node=node, opt='delproject', project=project)
        results = []
        for version in versions:
            url_listspiders = url_for('.manage', node=node, opt='listspiders', project=project,
                                      version_spider_job=version)
            url_delversion = url_for('.manage', node=node, opt='delversion', project=project,
                                     version_spider_job=version)
            try:
                version_readable = ' (%s)' % datetime.datetime.fromtimestamp(int(version)).isoformat()
            except:
                version_readable = ''
            results.append((version, version_readable, url_listspiders, url_delversion))
        return render_template('scrapydweb/listversions.html', node=node,
                               url_delproject=url_delproject, project=project,
                               node_name=node_name, results=results)

    elif opt == 'listspiders':
        spiders = js['spiders']
        results = []
        for spider in spiders:
            url_schedule = url_for('schedule.schedule', node=node, project=project, version=version_spider_job,
                                   spider=spider)
            url_multinode_schedule = url_for('overview.overview', node=node, opt='schedule', project=project,
                                             version_job=version_spider_job, spider=spider)
            results.append((spider, url_schedule, url_multinode_schedule))
        return render_template('scrapydweb/listspiders.html', node=node,
                               results=results)

    elif opt == 'delversion':
        return '<em style="color: red;">deleted</em>'

    elif opt == 'delproject':
        return '<em style="color: red;">deleted</em>'
