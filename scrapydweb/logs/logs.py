# coding: utf8
import os
import io
import time
import re

from flask import Blueprint, render_template, url_for, request, send_from_directory, flash
from flask import current_app as app

from ..vars import CACHE_PATH, INFO, WARN
from .utils import parse_log
from ..utils import make_request

CWD = os.path.dirname(os.path.abspath(__file__))
bp = Blueprint('logs', __name__, url_prefix='/')


@bp.route('/<int:node>/logs/<opt>/<project>/<spider>/<job>/', methods=('GET', 'POST'))
def logs(node, opt, project, spider, job):
    SIMPLEUI = True if request.args.get('ui', '') == 'simple' else False
    UI = 'simple' if SIMPLEUI else None
    TEMPLATE = 'scrapydweb/simpleui/%s.html' % opt if SIMPLEUI else 'scrapydweb/%s.html' % opt
    TEMPLATE_RESULT = 'scrapydweb/simpleui/result.html' if SIMPLEUI else 'scrapydweb/result.html'

    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVER = SCRAPYD_SERVERS[node - 1]
    LAST_LOG_ALERT_SECONDS = app.config.get('LAST_LOG_ALERT_SECONDS', 60)
    SCRAPYD_LOGS_DIR = app.config.get('SCRAPYD_LOGS_DIR', '')

    DISABLE_CACHE = app.config.get('DISABLE_CACHE', False)
    ENABLE_CACHE = True if (not SIMPLEUI) and (not DISABLE_CACHE) else False

    if ENABLE_CACHE:
        node_path = os.path.join(CACHE_PATH, re.sub(r'\.|\:', '_', SCRAPYD_SERVERS[node - 1]))
        project_path = os.path.join(node_path, project)
        spider_path = os.path.join(project_path, spider)
        if not os.path.isdir(CACHE_PATH):
            os.mkdir(CACHE_PATH)
        if not os.path.isdir(node_path):
            os.mkdir(node_path)
        if not os.path.isdir(project_path):
            os.mkdir(project_path)
        if not os.path.isdir(spider_path):
            os.mkdir(spider_path)
        filename = '%s_%s.html' % (job, opt)
        filepath = os.path.join(spider_path, filename)

    # Return cached html, cache.py should 'POST'
    if (ENABLE_CACHE
        and request.method == 'GET'
        and not request.args.get('no_cache', '')):
        if os.path.exists(filepath):
            return send_from_directory(spider_path, filename)

    # TODO: .txt
    url = 'http://{}/logs/{}/{}/{}.log'.format(SCRAPYD_SERVER, project, spider, job)

    text = ''
    if SCRAPYD_SERVER.split(':')[0] == '127.0.0.1' and SCRAPYD_LOGS_DIR:
        logfile = os.path.join(SCRAPYD_LOGS_DIR, project, spider, job + '.log')
        if os.path.exists(logfile):
            with io.open(logfile, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            flash("Using local logfile at %s " % logfile, INFO)
        else:
            flash("Local logfile %s NOT found, making request to Scrapyd server instead" % logfile, WARN)
    if not text:
        # cache.py use 'POST', and disable log
        log = False if request.method == 'POST' else True
        status_code, text = make_request(url, api=False, log=log)
        if status_code != 200:
            return render_template(TEMPLATE_RESULT, node=node,
                                   url=url, status_code=status_code, text=text)

    # To show 'refresh' button with '?no_cache=True'
    if ENABLE_CACHE:
        # http://flask.pocoo.org/docs/1.0/api/#flask.Request.url_root
        refresh_url = request.script_root + request.path + '?no_cache=True' + ('&ui=simple' if SIMPLEUI else '')
    else:
        refresh_url = ''

    if opt == 'utf8':
        url_stats = url_for('.logs', node=node, opt='stats', project=project, spider=spider, job=job, ui=UI)
        last_refresh_timestamp = time.time()
        html = render_template(TEMPLATE, node=node,
                               project=project, spider=spider,
                               url_source=url, url_stats=url_stats,
                               refresh_url=refresh_url, last_refresh_timestamp=last_refresh_timestamp,
                               LAST_LOG_ALERT_SECONDS=LAST_LOG_ALERT_SECONDS, text=text)
    elif opt == 'stats':
        kwargs = {
            'project': project,
            'spider': spider,
            'job': job,
            'url_source': url,
            'url_utf8': url_for('.logs', node=node, opt='utf8', project=project, spider=spider, job=job, ui=UI),
            'LAST_LOG_ALERT_SECONDS': LAST_LOG_ALERT_SECONDS,
            'refresh_url': refresh_url,
        }
        parse_log(text, kwargs)
        kwargs['last_refresh_timestamp'] = time.time()
        html = render_template(TEMPLATE, node=node, **kwargs)

    # Save as cache
    if ENABLE_CACHE:
        try:
            with io.open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(html)
        except Exception as err:
            flash("Fail to cache html to %s: %s %s" % (filepath, err.__class__.__name__, err), WARN)
            try:
                os.remove(filepath)
            except:
                pass

    return html
