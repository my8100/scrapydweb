# coding: utf8
import io
import os
import re
import time

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, send_from_directory
)
from flask import current_app as app
from werkzeug.utils import secure_filename

from ..vars import UPLOAD_PATH, WARN
from .utils import parse_log

CWD = os.path.dirname(os.path.abspath(__file__))
ALLOWED_EXTENSIONS = {'log', 'txt'}

bp = Blueprint('parse', __name__, url_prefix='/')


@bp.route('/<int:node>/log/upload/', methods=('GET', 'POST'))
def upload(node):
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    SIMPLEUI = True if request.args.get('ui', '') == 'simple' else False
    UI = 'simple' if SIMPLEUI else None
    TEMPLATE = 'scrapydweb/simpleui/parse.html' if SIMPLEUI else 'scrapydweb/parse.html'

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file selected', WARN)
            return redirect(request.url)

        file = request.files['file']
        # if user does not select file, browser also submit an empty part without filename
        if file.filename == '':
            flash('Filename not found', WARN)
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Only %s file type are supported' % ALLOWED_EXTENSIONS, WARN)
            return redirect(request.url)

        # Non-ASCII would be omitted and may set the filename as 'log' or 'txt'
        filename = secure_filename(file.filename)
        if filename in ALLOWED_EXTENSIONS:
            filename = '%s.%s' % (time.strftime('%Y-%m-%d_%H%M%S'), filename)
        file.save(os.path.join(UPLOAD_PATH, filename))

        return redirect(url_for('.uploaded', node=node, filename=filename, ui=UI))

    else:
        url_parse_demo = url_for('.uploaded', node=node, filename='demo.txt', ui=UI)
        return render_template(TEMPLATE, node=node,
                               url_parse_demo=url_parse_demo)


@bp.route('/<int:node>/log/uploaded/<filename>')
def uploaded(node, filename):
    SIMPLEUI = True if request.args.get('ui', '') == 'simple' else False
    TEMPLATE = 'scrapydweb/simpleui/stats.html' if SIMPLEUI else 'scrapydweb/stats.html'
    TEMPLATE_RESULT = 'scrapydweb/simpleui/result.html' if SIMPLEUI else 'scrapydweb/result.html'

    try:
        # Use io.open for python2 compatibility
        with io.open(os.path.join(UPLOAD_PATH, filename), encoding='utf8', errors='ignore') as f:
            text = f.read()
    except Exception as err:
        text = '%s\n%s' % (err.__class__.__name__, err)
        return render_template(TEMPLATE_RESULT, node=node,
                               text="An error occurred when reading the uploaded log file:\n\n%s" % text)

    # 2018-08-21 12:21:45 [scrapy.utils.log] INFO: Scrapy 1.5.0 started (bot: proxy)
    m = re.search(r'\(bot:\s(.+?)\)', text)
    project = m.group(1) if m else ''

    # 2018-08-21 12:21:45 [test] DEBUG: from_crawler
    m = re.search(r'\[([^\.]+?)\]\s+(?:DEBUG|INFO|WARNING|ERROR|CRITICAL)', text)
    spider = m.group(1) if m else ''

    # 'LOG_FILE': 'logs\\proxy\\test\\b2095ab0a4f911e8b98614dda9e91c2f.log',
    m = re.search(r'LOG_FILE.*?([\w-]+)\.(?:log|log\.gz|gz|txt)', text)
    job = m.group(1) if m else (filename.rpartition('.')[0] or filename)

    kwargs = {
        'project': project,
        'spider': spider,
        'job': job,
        'url_source': url_for('.source', filename=filename),
        # 'url_utf8': url_utf8, # to hide url_utf8 link in page http://127.0.0.1:5000/log/uploaded/demo.txt
        'LAST_LOG_ALERT_SECONDS': app.config.get('LAST_LOG_ALERT_SECONDS', 60),
    }
    parse_log(text, kwargs)
    kwargs['last_refresh_timestamp'] = time.time()
    return render_template(TEMPLATE, node=node, **kwargs)


@bp.route('/log/source/<filename>')
def source(filename):
    return send_from_directory(UPLOAD_PATH, filename, mimetype='text/plain')
