# coding: utf8
from flask import Blueprint, render_template, request
from flask import current_app as app

bp = Blueprint('multinode', __name__, url_prefix='/')


@bp.route('/<int:node>/multinode/<opt>/<project>/<version_job>/', methods=('POST',))
@bp.route('/<int:node>/multinode/<opt>/<project>/', methods=('POST',))
def multinode(node, opt, project, version_job=None):
    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])

    if opt == 'stop':
        title = "STOP Project(%s) Job(%s)" % (project, version_job)
    elif opt == 'delproject':
        title = "DELETE Project(%s)" % project
    elif opt == 'delversion':
        title = "DELETE Project(%s) Version(%s)" % (project, version_job)

    selected_nodes = []
    for i in range(1, len(SCRAPYD_SERVERS) + 1):
        if request.form.get(str(i)) == 'on':
            selected_nodes.append(i)

    return render_template('scrapydweb/multinode_results.html', node=node,
                           opt=opt, project=project, version_job=version_job,
                           title=title, selected_nodes=selected_nodes)
