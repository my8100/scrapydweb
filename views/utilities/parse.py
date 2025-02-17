# coding: utf-8
import io
import os
import re

from flask import Blueprint, flash, redirect, render_template, request, send_from_directory, url_for
from logparser import parse
from werkzeug.utils import secure_filename

from ...vars import PARSE_PATH
from ..baseview import BaseView


ALLOWED_EXTENSIONS = {'log', 'txt'}
bp = Blueprint('parse', __name__, url_prefix='/')


@bp.route('/parse/source/<filename>')
def source(filename):
    return send_from_directory(PARSE_PATH, filename, mimetype='text/plain', cache_timeout=0)


class UploadLogView(BaseView):

    def __init__(self):
        super(UploadLogView, self).__init__()

        self.template = 'scrapydweb/parse.html'

    def dispatch_request(self, **kwargs):
        if self.POST:
            file = request.files.get('file')
            if not file:
                flash('No file selected', self.WARN)
                return redirect(request.url)

            if file.filename == '':
                flash('Filename not found', self.WARN)
                return redirect(request.url)

            if file.filename.rpartition('.')[-1] not in ALLOWED_EXTENSIONS:
                flash('Only file type of %s is supported' % ALLOWED_EXTENSIONS, self.WARN)
                return redirect(request.url)

            # Non-ASCII would be omitted and may set the filename as 'log' or 'txt'
            filename = secure_filename(file.filename)
            if filename in ALLOWED_EXTENSIONS:
                filename = '%s.%s' % (self.get_now_string(), filename)
            file.save(os.path.join(self.PARSE_PATH, filename))

            return redirect(url_for('.uploaded', node=self.node, filename=filename))
        else:
            url_parse_demo = url_for('.uploaded', node=self.node, filename='ScrapydWeb_demo.log')
            return render_template(self.template, node=self.node, url_parse_demo=url_parse_demo)


class UploadedLogView(BaseView):

    def __init__(self):
        super(UploadedLogView, self).__init__()

        self.filename = self.view_args['filename']
        self.template = 'scrapydweb/stats.html'

        self.text = ''
        self.project = ''
        self.spider = ''
        self.job = ''

    def dispatch_request(self, **kwargs):
        try:
            # Use io.open for compatibility with Python 2
            with io.open(os.path.join(self.PARSE_PATH, self.filename), encoding='utf-8', errors='ignore') as f:
                self.text = f.read()
        except Exception as err:
            return render_template(self.template_fail, node=self.node,
                                   alert="An error occurred when reading the uploaded logfile",
                                   text='%s\n%s' % (err.__class__.__name__, err))

        self.get_job_info()

        kwargs = dict(
            project=self.project,
            spider=self.spider,
            job=self.job,
            url_source=url_for('.source', filename=self.filename),
            # url_utf8=url_utf8, # To hide url_utf8 link in page http://127.0.0.1:5000/log/uploaded/ScrapydWeb_demo.log
        )
        kwargs.update(parse(self.text))
        # self.logger.debug("Parsed result: %s" % self.json_dumps(kwargs))
        return render_template(self.template, node=self.node, **kwargs)

    def get_job_info(self):
        # 2018-08-21 12:21:45 [scrapy.utils.log] INFO: Scrapy 1.5.0 started (bot: proxy)
        m_project = re.search(r'\(bot:\s(.+?)\)', self.text)
        self.project = m_project.group(1) if m_project else self.NA

        # 2018-08-21 12:21:45 [test] DEBUG: from_crawler
        m_spider = re.search(r'\[([^.]+?)\]\s+(?:DEBUG|INFO|WARNING|ERROR|CRITICAL)', self.text)
        self.spider = m_spider.group(1) if m_spider else self.NA

        # 'LOG_FILE': 'logs\\proxy\\test\\b2095ab0a4f911e8b98614dda9e91c2f.log',
        m_job = re.search(r'LOG_FILE.*?([\w-]+)\.(?:log|txt)', self.text)
        self.job = m_job.group(1) if m_job else (self.filename.rpartition('.')[0] or self.filename)
