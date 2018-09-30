# coding: utf8
from flask import Blueprint, url_for, request, redirect
from flask import current_app as app


bp = Blueprint('index', __name__, url_prefix='/')
check_latest_version = True


# http://flask.pocoo.org/docs/1.0/quickstart/#routing
# int accepts positive integers
@bp.route('/<int:node>/')
@bp.route('/')
def index(node=1):
    SIMPLEUI = True if request.args.get('ui', '') == 'simple' else False
    UI = 'simple' if SIMPLEUI else None
    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])

    if SIMPLEUI or len(SCRAPYD_SERVERS) == 1:
        return redirect(url_for('dashboard.dashboard', node=node, ui=UI))
    else:
        return redirect(url_for('overview.overview', node=node))
