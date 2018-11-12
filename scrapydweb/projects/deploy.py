# coding: utf8
import os
import sys
import io
import glob
import time
from datetime import datetime
import re
import tempfile
import zipfile
import tarfile
from shutil import copyfile, rmtree

from .scrapyd_deploy import _build_egg
from flask import render_template, request, url_for, redirect
from werkzeug.utils import secure_filename

from ..myview import MyView
from .utils import slot
from ..vars import DEPLOY_PATH


PY2 = True if sys.version_info[0] < 3 else False


class DeployView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.url = 'http://{}/{}.json'.format(self.SCRAPYD_SERVER, 'addversion')
        self.template = 'scrapydweb/deploy.html'

    def dispatch_request(self, **kwargs):
        # python2 'ascii' codec can't decode byte
        scrapy_cfg_list = glob.glob(os.path.join(self.SCRAPY_PROJECTS_DIR, '*', u'scrapy.cfg'))
        projects_list = [os.path.dirname(i) for i in scrapy_cfg_list]

        kwargs = dict(
            node=self.node,
            url=self.url,
            selected_nodes=self.get_selected_nodes(),
            projects=[os.path.basename(i) for i in projects_list],
            modification_times=[self.get_modification_time(i) for i in projects_list],
            SCRAPY_PROJECTS_DIR=self.SCRAPY_PROJECTS_DIR
        )
        return render_template(self.template, **kwargs)

    @staticmethod
    def get_modification_time(path):
        # https://stackoverflow.com/a/29685234/10517783
        # https://stackoverflow.com/a/13454267/10517783
        filepath_list = []

        in_top_dir = True
        for dirpath, dirnames, filenames in os.walk(path):
            if in_top_dir:
                in_top_dir = False
                dirnames[:] = [d for d in dirnames if d not in ['build', 'project.egg-info']]
                filenames = [f for f in filenames if not f.endswith('.egg')]
            for filename in filenames:
                filepath_list.append(os.path.join(dirpath, filename))
        max_timestamp = max([os.path.getmtime(f) for f in filepath_list] or [time.time()])
        return datetime.fromtimestamp(max_timestamp).strftime('%Y-%m-%dT%H_%M_%S')


class UploadView(MyView):
    methods = ['POST']

    def __init__(self):
        super(self.__class__, self).__init__()

        self.url = ''
        self.template = 'scrapydweb/deploy_results.html'
        self.template_result = 'scrapydweb/result.html'

        self.project_original = ''
        self.project = ''
        self.version = ''
        self.selected_nodes_amount = int(request.form.get('checked_amount', 0))
        self.selected_nodes = []
        self.first_selected_node = 0

        self.eggname = ''
        self.eggpath = ''
        self.scrapy_cfg_path = ''
        self.scrapy_cfg_searched_paths = []
        self.scrapy_cfg_not_found = False
        self.data = None

        self.slot = slot

    def dispatch_request(self, **kwargs):
        self.handle_form()

        if self.scrapy_cfg_not_found:
            text = "scrapy.cfg NOT found"
            if self.selected_nodes_amount > 1:
                alert = "Multinode deployment terminated: %s" % text
            else:
                alert = "Fail to deploy project: %s" % text
            return render_template('scrapydweb/result.html', node=self.node,
                                   alert=alert, text=text,
                                   message=self.json_dumps(self.scrapy_cfg_searched_paths))
        else:
            self.prepare_data()
            status_code, js = self.make_request(self.url, self.data, auth=self.AUTH)

        if js['status'] != 'ok':
            # With multinodes, would try to deploy to the first selected node first
            if self.selected_nodes_amount > 1:
                alert = ("Multinode deployment terminated, "
                         "since the first selected node returned status: " + js['status'])
            else:
                alert = "Fail to deploy project, got status: " + js['status']
            message = js.get('message', '')
            if message:
                js.update({'message': 'See details below'})

            return render_template(self.template_result, node=self.node,
                                   alert=alert, text=self.json_dumps(js), message=message)
        else:
            if self.selected_nodes_amount == 0:
                return redirect(url_for('schedule.schedule', node=self.node,
                                        project=self.project, version=self.version))
            else:
                kwargs = dict(
                    node=self.node,
                    selected_nodes=self.selected_nodes,
                    first_selected_node=self.first_selected_node,
                    js=js,
                    eggname=self.eggname,
                    project=self.project,
                    version=self.version
                )
                return render_template(self.template, **kwargs)

    def handle_form(self):
        # {'1': 'on',
        # '2': 'on',
        # 'checked_amount': '2',
        # 'project': 'demo',
        # 'version': '2018-09-05T03_13_50'}

        # With multinodes, would try to deploy to the first selected node first
        if self.selected_nodes_amount:
            self.selected_nodes = self.get_selected_nodes()
            self.first_selected_node = self.selected_nodes[0]
            self.url = 'http://{}/{}.json'.format(self.SCRAPYD_SERVERS[self.first_selected_node - 1], 'addversion')
        else:
            self.url = 'http://{}/{}.json'.format(self.SCRAPYD_SERVERS[self.node - 1], 'addversion')

        self.project_original = request.form.get('project', '')  # Used with SCRAPY_PROJECTS_DIR to get project_path
        self.project = re.sub(r'[^0-9A-Za-z_-]', '', self.project_original) or self.get_now_string()
        self.version = re.sub(r'[^0-9A-Za-z_-]', '', request.form.get('version', '')) or self.get_now_string()

        if request.files.get('file'):
            self.handle_uploaded_file()
        else:
            self.handle_local_project()

    def handle_local_project(self):
        # Use project_original instead of project
        project_path = os.path.join(self.SCRAPY_PROJECTS_DIR, self.project_original)

        self.search_scrapy_cfg_path(project_path)
        if not self.scrapy_cfg_path:
            self.scrapy_cfg_not_found = True
            return

        self.eggname = '%s_%s.egg' % (self.project, self.version)
        self.eggpath = os.path.join(DEPLOY_PATH, self.eggname)
        self.build_egg()

    def handle_uploaded_file(self):
        # http://flask.pocoo.org/docs/1.0/api/#flask.Request.form
        # <class 'werkzeug.datastructures.FileStorage'>
        file = request.files['file']

        # Non-ASCII would be omitted and may set the eggname as to 'egg'
        filename = secure_filename(file.filename)
        if filename in ['egg', 'zip', 'tar', 'tar.gz']:
            filename = '%s_%s.%s' % (self.project, self.version, filename)
        else:
            filename = '%s_%s_from_file_%s' % (self.project, self.version, filename)

        if filename.endswith('egg'):
            self.eggname = filename
            self.eggpath = os.path.join(DEPLOY_PATH, self.eggname)
            file.save(self.eggpath)
            self.scrapy_cfg_not_found = False
        else:  # Compressed file
            filepath = os.path.join(DEPLOY_PATH, filename)
            file.save(filepath)
            tmpdir = self.uncompress_to_tmpdir(filepath)

            # Search from the root of tmpdir
            self.search_scrapy_cfg_path(tmpdir)
            if not self.scrapy_cfg_path:
                self.scrapy_cfg_not_found = True
                return

            self.eggname = re.sub(r'(\.zip|\.tar|\.tar\.gz)$', '.egg', filename)
            self.eggpath = os.path.join(DEPLOY_PATH, self.eggname)
            self.build_egg()

    def uncompress_to_tmpdir(self, filepath):
        self.logger.debug("Uncompress %s" % filepath)
        tmpdir = tempfile.mkdtemp(prefix="scrapydweb-uncompress-")
        tmpdir_ = tempfile.mkdtemp(prefix="scrapydweb-uncompress-")
        if zipfile.is_zipfile(filepath):
            with zipfile.ZipFile(filepath, 'r') as f:
                if PY2:
                    for filename in f.namelist():
                        f.extract(filename, tmpdir_)
                        # https://gangmax.me/blog/2011/09/17/12-14-52-publish-532/
                        # When ScrapydWeb runs in Linux and tries to uncompress zip file that compressed in Windows
                        try:
                            filename_utf8 = filename.decode('gbk').encode('utf8')
                        except UnicodeDecodeError:
                            filename_utf8 = filename
                        filepath_ = os.path.join(tmpdir_, filename)
                        filepath_utf8 = os.path.join(tmpdir, filename_utf8)
                        if os.path.isdir(filepath_):
                            os.mkdir(filepath_utf8)
                        else:
                            copyfile(filepath_, filepath_utf8)
                else:
                    f.extractall(tmpdir)
                    f.close()
        else:  # 'tar' 'tar.gz'
            with tarfile.open(filepath, 'r') as f:  # Open for reading with transparent compression (recommended).
                f.extractall(tmpdir)
                f.close()

        self.logger.debug("Uncompress to %s" % tmpdir)
        # In case uploading a compressed file in which scrapy_cfg_dir contains none ascii in python 2,
        # whereas selecting a project when auto eggifying, scrapy_cfg_dir is unicode
        # print(repr(tmpdir))
        # print(type(tmpdir))
        return tmpdir.decode('utf8') if PY2 else tmpdir

    def search_scrapy_cfg_path(self, search_path):
        for dirpath, dirnames, filenames in os.walk(search_path):
            self.scrapy_cfg_searched_paths.append(os.path.abspath(dirpath))
            self.scrapy_cfg_path = os.path.abspath(os.path.join(dirpath, 'scrapy.cfg'))
            if os.path.exists(self.scrapy_cfg_path):
                self.logger.debug("scrapy_cfg_path: %s" % self.scrapy_cfg_path)
                return

        self.logger.error("scrapy.cfg NOT found in: %s" % search_path)
        self.scrapy_cfg_path = ''

    def build_egg(self):
        egg, tmpdir = _build_egg(self.scrapy_cfg_path)

        scrapy_cfg_dir = os.path.dirname(self.scrapy_cfg_path)
        copyfile(egg, os.path.join(scrapy_cfg_dir, self.eggname))
        copyfile(egg, self.eggpath)
        rmtree(tmpdir)
        self.logger.debug("egg file saved to: %s" % self.eggpath)

    def prepare_data(self):
        with io.open(self.eggpath, 'rb') as f:
            content = f.read()
            self.data = {
                'project': self.project,
                'version': self.version,
                'egg': content
            }

        self.slot.add_egg(self.eggname, content)


class DeployXhrView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.eggname = self.view_args['eggname']
        self.project = self.view_args['project']
        self.version = self.view_args['version']

        self.url = 'http://{}/{}.json'.format(self.SCRAPYD_SERVER, 'addversion')

        self.slot = slot

    def dispatch_request(self, **kwargs):
        content = self.slot.egg.get(self.eggname)
        if not content:
            eggpath = os.path.join(DEPLOY_PATH, self.eggname)
            with io.open(eggpath, 'rb') as f:
                content = f.read()

        data = {
            'project': self.project,
            'version': self.version,
            'egg': content
        }
        status_code, js = self.make_request(self.url, data, auth=self.AUTH)
        return self.json_dumps(js)
