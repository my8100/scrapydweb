# coding: utf8
import re

from flask import Blueprint, render_template, flash, request
from flask import current_app as app

from ..vars import INFO, WARN, pattern_jobs, keys_jobs
from ..utils import make_request

bp = Blueprint('dashboard', __name__, url_prefix='/')
check_latest_version = True


@bp.route('/<int:node>/dashboard/')
def dashboard(node):
    SIMPLEUI = True if request.args.get('ui', '') == 'simple' else False
    UI = 'simple' if SIMPLEUI else None
    TEMPLATE = 'scrapydweb/simpleui/index.html' if SIMPLEUI else 'scrapydweb/dashboard.html'
    TEMPLATE_RESULT = 'scrapydweb/simpleui/result.html' if SIMPLEUI else 'scrapydweb/result.html'

    # http://flask.pocoo.org/docs/1.0/appcontext/#lifetime-of-the-context
    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVER = SCRAPYD_SERVERS[node - 1]
    SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])
    SCRAPYDWEB_BIND = app.config.get('SCRAPYDWEB_BIND', '0.0.0.0')
    SCRAPYDWEB_PORT = app.config.get('SCRAPYDWEB_PORT', 5000)
    SHOW_DASHBOARD_JOB_COLUMN = app.config.get('SHOW_DASHBOARD_JOB_COLUMN', False)
    DASHBORAD_RELOAD_INTERVAL = int(app.config.get('DASHBORAD_RELOAD_INTERVAL', 300))

    scrapydweb_url = 'http://%s:%s' % (SCRAPYDWEB_BIND, SCRAPYDWEB_PORT)

    url = 'http://%s/jobs' % SCRAPYD_SERVER
    auth = SCRAPYD_SERVERS_AUTHS[node - 1]
    url_auth = url.replace('http://', 'http://%s:%s@' % auth) if auth else url
    status_code, text = make_request(url, api=False, auth=auth)

    if status_code != 200 or not re.search(r'Jobs', text):
        return render_template(TEMPLATE_RESULT, node=node,
                               url=url_auth, status_code=status_code, text=text)

    rows = [dict(zip(keys_jobs, row)) for row in pattern_jobs.findall(text)]

    pending_rows = []
    running_rows = []
    finished_rows = []
    for row in rows:
        # <a href='/items/demo/test/2018-10-12_205507.jl'>Items</a>
        if row['items']:
            row['url_items'] = url_auth[:-5] + re.search(r"href='(.*?)'>", row['items']).group(1)

        if not row['start']:
            pending_rows.append(row)
        elif not row['finish']:
            running_rows.append(row)
        else:
            finished_rows.append(row)

    if SIMPLEUI:
        flash("<a href='/'>Visit New UI</a> to get full features.", INFO)

    if app.config.get('DISABLE_CACHE', False):
        flash("Caching for utf8 and stats html is NOT working \
              since ScrapydWeb is running with argument '--disable_cache'.", WARN)

    if SCRAPYD_SERVER.split(':')[0] == '127.0.0.1' and not app.config.get('SCRAPYD_LOGS_DIR', ''):
        flash("Run ScrapydWeb with argument '--scrapyd_logs_dir SCRAPYD_LOGS_DIR' \
              to speed up loading utf8 and stats html.", INFO)

    return render_template(TEMPLATE, node=node,
                           ui=UI, colspan=12, url=url_auth,
                           scrapydweb_url=scrapydweb_url, pending_rows=pending_rows,
                           running_rows=running_rows, finished_rows=finished_rows,
                           SHOW_DASHBOARD_JOB_COLUMN=SHOW_DASHBOARD_JOB_COLUMN,
                           DASHBORAD_RELOAD_INTERVAL=DASHBORAD_RELOAD_INTERVAL)
