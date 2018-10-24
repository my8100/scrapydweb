# coding: utf8
import os
import io
import time
import re

from flask import Blueprint, render_template, url_for, request, send_from_directory, flash
from flask import current_app as app

from ..vars import CACHE_PATH, INFO, WARN, ALLOWED_SCRAPYD_LOG_EXTENSIONS
from .utils import parse_log
from ..utils import make_request


bp = Blueprint('log', __name__, url_prefix='/')


@bp.route('/<int:node>/log/<opt>/<project>/<spider>/<job>/<ext>/', methods=('GET', 'POST'))
@bp.route('/<int:node>/log/<opt>/<project>/<spider>/<job>/', methods=('GET', 'POST'))
def log(node, opt, project, spider, job, ext=None):
    SIMPLEUI = True if request.args.get('ui', '') == 'simple' else False
    UI = 'simple' if SIMPLEUI else None
    TEMPLATE_UTF8 = 'scrapydweb/simpleui/utf8.html' if SIMPLEUI else 'scrapydweb/utf8.html'
    TEMPLATE_STATS = 'scrapydweb/simpleui/stats.html' if SIMPLEUI else 'scrapydweb/stats.html'
    TEMPLATE_RESULT = 'scrapydweb/simpleui/result.html' if SIMPLEUI else 'scrapydweb/result.html'

    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVER = SCRAPYD_SERVERS[node - 1]
    SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])
    LAST_LOG_ALERT_SECONDS = app.config.get('LAST_LOG_ALERT_SECONDS', 60)
    SCRAPYD_LOGS_DIR = app.config.get('SCRAPYD_LOGS_DIR', '')
    if ext is None:
        SCRAPYD_LOG_EXTENSIONS = app.config.get('SCRAPYD_LOG_EXTENSIONS', []) or ALLOWED_SCRAPYD_LOG_EXTENSIONS
    else:
        SCRAPYD_LOG_EXTENSIONS = ['']

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

    # Return cached html, cache.py should 'POST'
    if (ENABLE_CACHE
        and request.method == 'GET'
        and not request.args.get('no_cache', '')):
        htmlname = '%s_%s.html' % (job, opt)
        htmlpath = os.path.join(spider_path, htmlname)
        if os.path.exists(htmlpath):
            return send_from_directory(spider_path, htmlname)

    # UnicodeEncodeError: 'ascii' codec can't encode characters in position 20-21: ordinal not in range(128)
    url_without_ext = u'http://{}/logs/{}/{}/{}'.format(SCRAPYD_SERVER, project, spider, job)
    url = url_without_ext
    auth = SCRAPYD_SERVERS_AUTHS[node - 1]
    url_auth = url.replace('http://', 'http://%s:%s@' % auth) if auth else url
    # Default extension .log for cached html
    url_auth += '.log'

    text = ''
    if SCRAPYD_SERVER.split(':')[0] == '127.0.0.1' and SCRAPYD_LOGS_DIR:
        found = False
        for ext in SCRAPYD_LOG_EXTENSIONS:
            logfile = os.path.join(SCRAPYD_LOGS_DIR, project, spider, job + ext)
            if os.path.exists(logfile):
                with io.open(logfile, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                flash("Using local logfile at %s " % logfile, INFO)
            found = True
            break
        if not found:
            flash("Local logfile %s NOT found, making request to Scrapyd server instead" % logfile, WARN)
    if not text:
        # cache.py use 'POST', and disable log
        log = False if request.method == 'POST' else True
        for ext in SCRAPYD_LOG_EXTENSIONS:
            url = '%s%s' % (url_without_ext, ext)
            url_auth = url.replace('http://', 'http://%s:%s@' % auth) if auth else url
            status_code, text = make_request(url, api=False, log=log, auth=auth)
            if status_code == 200:
                break
        if status_code != 200:
            return render_template(TEMPLATE_RESULT, node=node,
                                   url=url_auth, status_code=status_code, text=text)


    # To show 'refresh' button with '?no_cache=True'
    if ENABLE_CACHE:
        # http://flask.pocoo.org/docs/1.0/api/#flask.Request.url_root
        refresh_url = request.script_root + request.path + '?no_cache=True' + ('&ui=simple' if SIMPLEUI else '')
    else:
        refresh_url = ''

    # Generate html_utf8
    # url_stats = url_for('.log', node=node, opt='stats', project=project, spider=spider, job=job, ui=UI)
    url_stats = request.url.replace('/log/utf8/', '/log/stats/')
    html_utf8 = render_template(TEMPLATE_UTF8, node=node,
                           project=project, spider=spider,
                           url_source=url_auth, url_stats=url_stats,
                           refresh_url=refresh_url.replace('/log/stats/', '/log/utf8/'), 
                           last_refresh_timestamp=time.time(),
                           LAST_LOG_ALERT_SECONDS=LAST_LOG_ALERT_SECONDS, text=text)
    # Generate html_stats
    kwargs = {
        'project': project,
        'spider': spider,
        'job': job,
        'url_source': url_auth,
        # 'url_utf8': url_for('.log', node=node, opt='utf8', project=project, spider=spider, job=job, ui=UI),
        'url_utf8': request.url.replace('/log/stats/', '/log/utf8/'),
        'LAST_LOG_ALERT_SECONDS': LAST_LOG_ALERT_SECONDS,
        'refresh_url': refresh_url.replace('/log/utf8/', '/log/stats/'),
    }
    parse_log(text, kwargs)
    kwargs['last_refresh_timestamp'] = time.time()
    html_stats = render_template(TEMPLATE_STATS, node=node, **kwargs)

    # Save cache file
    if ENABLE_CACHE:
        for opt_, html in zip(['utf8', 'stats'], [html_utf8, html_stats]):
            htmlname = '%s_%s.html' % (job, opt_)
            htmlpath = os.path.join(spider_path, htmlname)
            try:
                with io.open(htmlpath, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(html)
            except Exception as err:
                print("Fail to cache html to %s: %s %s" % (htmlpath, err.__class__.__name__, err))
                try:
                    os.remove(htmlpath)
                except:
                    pass
            # else:
                # print(htmlpath)

    return html_utf8 if opt == 'utf8' else html_stats
