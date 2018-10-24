# coding: utf8
from flask import Blueprint, render_template, flash, request
from flask import current_app as app

from ..vars import INFO

bp = Blueprint('overview', __name__, url_prefix='/')
check_latest_version = True


@bp.route('/<int:node>/overview/<opt>/<project>/<version_job>/<spider>/', methods=('GET', 'POST'))
@bp.route('/<int:node>/overview/<opt>/<project>/<version_job>/', methods=('GET', 'POST'))
@bp.route('/<int:node>/overview/<opt>/<project>/', methods=('GET', 'POST'))
@bp.route('/<int:node>/overview/', methods=('GET', 'POST'))
def overview(node, opt=None, project=None, version_job=None, spider=None):
    global check_latest_version
    check_latest_version_ = check_latest_version
    if check_latest_version:
        check_latest_version = False

    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVER = SCRAPYD_SERVERS[node - 1]
    SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])
    url = 'http://%s/daemonstatus.json' % SCRAPYD_SERVER
    auth = SCRAPYD_SERVERS_AUTHS[node - 1]
    url_auth = url.replace('http://', 'http://%s:%s@' % auth) if auth else url


    if len(SCRAPYD_SERVERS) == 1:
        flash("Run ScrapydWeb with argument '-ss 127.0.0.1 -ss username:password@192.168.123.123:6801#group' \
              to set any number of Scrapyd servers to control.", INFO)

    if not(app.config.get('USERNAME', '') and app.config.get('PASSWORD', '')):
        flash("Run ScrapydWeb with argument '--username USERNAME --password PASSWORD' to enable basic auth.", INFO)

    if request.method == 'POST':
        selected_nodes = []
        for i in range(1, len(SCRAPYD_SERVERS) + 1):
            if request.form.get(str(i)) == 'on':
                selected_nodes.append(i)
    else:
        if len(SCRAPYD_SERVERS) == 1:
            selected_nodes = [1]
        else:
            selected_nodes = []

    return render_template('scrapydweb/overview.html', node=node,
                           check_latest_version=check_latest_version_,
                           opt=opt, project=project, version_job=version_job, spider=spider,
                           selected_nodes=selected_nodes, url=url_auth)
