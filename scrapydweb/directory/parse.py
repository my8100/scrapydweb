# coding: utf8
import io
import os
import re
import time

from flask import Blueprint, flash, redirect, render_template, request, url_for, send_from_directory
from werkzeug.utils import secure_filename

from ..myview import MyView
from ..vars import PARSE_PATH, WARN
from .utils import parse_log


ALLOWED_EXTENSIONS = {'log', 'txt'}
bp = Blueprint('parse', __name__, url_prefix='/')


@bp.route('/parse/source/<filename>')
def source(filename):
    return send_from_directory(PARSE_PATH, filename, mimetype='text/plain')


class UploadLogView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.template = 'scrapydweb/simpleui/parse.html' if self.IS_SIMPLEUI else 'scrapydweb/parse.html'

    def dispatch_request(self, **kwargs):
        if self.POST:
            file = request.files.get('file')
            if not file:
                flash('No file selected', WARN)
                return redirect(request.url)

            if file.filename == '':
                flash('Filename not found', WARN)
                return redirect(request.url)

            if file.filename.rpartition('.')[-1] not in ALLOWED_EXTENSIONS:
                flash('Only file type of %s is supported' % ALLOWED_EXTENSIONS, WARN)
                return redirect(request.url)

            # Non-ASCII would be omitted and may set the filename as 'log' or 'txt'
            filename = secure_filename(file.filename)
            if filename in ALLOWED_EXTENSIONS:
                filename = '%s.%s' % (self.get_now_string(), filename)
            file.save(os.path.join(PARSE_PATH, filename))

            return redirect(url_for('.uploaded', node=self.node, filename=filename, ui=self.UI))
        else:
            url_parse_demo = url_for('.uploaded', node=self.node, filename='demo.txt', ui=self.UI)
            return render_template(self.template, node=self.node, url_parse_demo=url_parse_demo)


class UploadedLogView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.filename = self.view_args['filename']
        self.template = 'scrapydweb/simpleui/stats.html' if self.IS_SIMPLEUI else 'scrapydweb/stats.html'

        self.text = ''
        self.project = ''
        self.spider = ''
        self.job = ''

    def dispatch_request(self, **kwargs):
        try:
            # Use io.open for compatibility with Python 2
            with io.open(os.path.join(PARSE_PATH, self.filename), encoding='utf8', errors='ignore') as f:
                self.text = f.read()
        except Exception as err:
            return render_template(self.template_result, node=self.node,
                                   message='%s\n%s' % (err.__class__.__name__, err),
                                   text="An error occurred when reading the uploaded log file")

        self.get_job_info()

        kwargs = dict(
            project=self.project,
            spider=self.spider,
            job=self.job,
            url_source=url_for('.source', filename=self.filename),
            # url_utf8=url_utf8, # To hide url_utf8 link in page http://127.0.0.1:5000/log/uploaded/demo.txt
            LAST_LOG_ALERT_SECONDS=self.LAST_LOG_ALERT_SECONDS
        )

        parse_log(self.text, kwargs)
        kwargs['last_refresh_timestamp'] = time.time()

        return render_template(self.template, node=self.node, **kwargs)

    def get_job_info(self):
        # 2018-08-21 12:21:45 [scrapy.utils.log] INFO: Scrapy 1.5.0 started (bot: proxy)
        m_project = re.search(r'\(bot:\s(.+?)\)', self.text)
        self.project = m_project.group(1) if m_project else ''

        # 2018-08-21 12:21:45 [test] DEBUG: from_crawler
        m_spider = re.search(r'\[([^.]+?)\]\s+(?:DEBUG|INFO|WARNING|ERROR|CRITICAL)', self.text)
        self.spider = m_spider.group(1) if m_spider else ''

        # 'LOG_FILE': 'logs\\proxy\\test\\b2095ab0a4f911e8b98614dda9e91c2f.log',
        m_job = re.search(r'LOG_FILE.*?([\w-]+)\.(?:log|txt)', self.text)
        self.job = m_job.group(1) if m_job else (self.filename.rpartition('.')[0] or self.filename)
