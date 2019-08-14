# coding: utf-8
from functools import partial
import io
import os
import re

from flask import url_for

from scrapydweb.vars import DEMO_PROJECTS_PATH
from tests.utils import cst, req_single_scrapyd, set_single_scrapyd, upload_file_deploy


def test_auto_packaging_select_option(app, client):
    ins = [
        '(14 projects)',
        u"var folders = ['demo - 副本', 'demo',",
        "var projects = ['demo-copy', 'demo',",
        '<div>%s<' % cst.PROJECT,
        u'<div>demo - 副本<',
        '<div>demo<',
        '<div>demo_only_scrapy_cfg<'
    ]
    nos = ['<div>demo_without_scrapy_cfg<', '<h3>No projects found']
    req_single_scrapyd(app, client, view='deploy', kws=dict(node=1), ins=ins, nos=nos)

    for project in [cst.PROJECT, 'demo']:
        with io.open(os.path.join(cst.ROOT_DIR, 'data/%s/test' % project), 'w', encoding='utf-8') as f:
            f.write(u'')
        ins = ['id="folder_selected" value="%s"' % project, 'id="folder_selected_statement">%s<' % project]
        req_single_scrapyd(app, client, view='deploy', kws=dict(node=1), ins=ins)

    with io.open(os.path.join(cst.ROOT_DIR, 'data/demo/test'), 'w', encoding='utf-8') as f:
        f.write(u'')

    # SCRAPY_PROJECTS_DIR=os.path.join(cst.ROOT_DIR, 'data'),
    app.config['SCRAPY_PROJECTS_DIR'] = os.path.join(cst.ROOT_DIR, 'not-exist')
    req_single_scrapyd(app, client, view='deploy', kws=dict(node=1),
                       ins=['(0 projects)', '<h3>No projects found'])

    app.config['SCRAPY_PROJECTS_DIR'] = os.path.join(cst.ROOT_DIR, 'data', 'one_project_inside')
    req_single_scrapyd(app, client, view='deploy', kws=dict(node=1),
                       ins='(1 project)', nos='<h3>No projects found')

    if not os.environ.get('DATA_PATH', ''):
        app.config['SCRAPY_PROJECTS_DIR'] = ''
        req_single_scrapyd(app, client, view='deploy', kws=dict(node=1),
                           ins=DEMO_PROJECTS_PATH.replace('\\', '/'), nos='<h3>No projects found')


# {'status': 'error', 'message': 'Traceback
# ...TypeError:...activate_egg(eggpath)...\'tuple\' object is not an iterator\r\n'}
def test_addversion(app, client):
    data = {
        'project': 'fakeproject',
        'version': 'fakeversion',
        'file': (io.BytesIO(b'my file contents'), "fake.egg")
    }
    req_single_scrapyd(app, client, view='deploy.upload', kws=dict(node=1), data=data, ins='activate_egg')


# <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
# <title>Redirecting...</title>
# <h1>Redirecting...</h1>
# <p>You should be redirected automatically to target URL:
# <a href="/1/schedule/demo/2018-01-01T01_01_01/">/1/schedule/demo/2018-01-01T01_01_01/</a>.  If not click the link.
def test_auto_packaging(app, client):
    data = {
        'folder': cst.PROJECT,
        'project': cst.PROJECT,
        'version': cst.VERSION,
    }
    with app.test_request_context():
        # http://localhost/1/schedule/ScrapydWeb_demo/2018-01-01T01_01_01/
        req_single_scrapyd(app, client, view='deploy.upload', kws=dict(node=1), data=data,
                           location=url_for('schedule', node=1, project=cst.PROJECT, version=cst.VERSION))


def test_auto_packaging_unicode(app, client):
    if cst.WINDOWS_NOT_CP936:
        return
    data = {
        'folder': u'demo - 副本',
        'project': u'demo - 副本',
        'version': cst.VERSION,
    }
    with app.test_request_context():
        req_single_scrapyd(app, client, view='deploy.upload', kws=dict(node=1), data=data,
                           location=url_for('schedule', node=1, project='demo_____', version=cst.VERSION))


def test_scrapy_cfg(app, client):
    with app.test_request_context():
        for folder, result in cst.SCRAPY_CFG_DICT.items():
            data = {
                'folder': folder,
                'project': cst.PROJECT,
                'version': cst.VERSION,
            }
            if result:
                req_single_scrapyd(app, client, view='deploy.upload', kws=dict(node=1), data=data, ins=result)
            else:
                location = url_for('schedule', node=1, project=cst.PROJECT, version=cst.VERSION)
                req_single_scrapyd(app, client, view='deploy.upload', kws=dict(node=1), data=data, location=location)


def test_scrapy_cfg_node_not_exist(app, client):
    with app.test_request_context():
        for folder, result in cst.SCRAPY_CFG_DICT.items():
            data = {
                'folder': folder,
                'project': cst.PROJECT,
                'version': cst.VERSION,
            }
            nos = []
            if folder == 'demo_only_scrapy_cfg' or not result:
                ins = 'Fail to deploy project, got status'
            else:
                ins = ['Fail to deploy', result]
                nos = 'got status'
            req_single_scrapyd(app, client, view='deploy.upload', kws=dict(node=1), data=data,
                               ins=ins, nos=nos, set_to_second=True)


def test_upload_file_deploy(app, client):
    set_single_scrapyd(app)

    upload_file_deploy_singlenode = partial(upload_file_deploy, app=app, client=client, multinode=False)

    filenames = ['demo.egg', 'demo_inner.zip', 'demo_outer.zip',
                 'demo - Win7CNsendzipped.zip', 'demo - Win10cp1252.zip']
    if cst.WINDOWS_NOT_CP936:
        filenames.extend(['demo - Ubuntu.zip', 'demo - Ubuntu.tar.gz', 'demo - macOS.zip', 'demo - macOS.tar.gz'])
    else:
        filenames.extend([u'副本.zip', u'副本.tar.gz', u'副本.egg', u'demo - 副本 - Win7CN.zip',
                          u'demo - 副本 - Win7CNsendzipped.zip', u'demo - 副本 - Win10cp936.zip',
                          u'demo - 副本 - Ubuntu.zip', u'demo - 副本 - Ubuntu.tar.gz',
                          u'demo - 副本 - macOS.zip', u'demo - 副本 - macOS.tar.gz'])

    for filename in filenames:
        if filename == 'demo.egg':
            project = cst.PROJECT
            redirect_project = cst.PROJECT
        else:
            project = re.sub(r'\.egg|\.zip|\.tar\.gz', '', filename)
            project = 'demo_unicode' if project == u'副本' else project
            redirect_project = re.sub(cst.STRICT_NAME_PATTERN, '_', project)
        upload_file_deploy_singlenode(filename=filename, project=project, redirect_project=redirect_project)

    for filename, alert in cst.SCRAPY_CFG_DICT.items():
        if alert:
            upload_file_deploy_singlenode(filename='%s.zip' % filename, project=filename, alert=alert, fail=True)
        else:
            upload_file_deploy_singlenode(filename='%s.zip' % filename, project=filename, redirect_project=filename)

    app.config['SCRAPYD_SERVERS'] = ['not-exist:6801']

    for filename, alert in cst.SCRAPY_CFG_DICT.items():
        if filename == 'demo_only_scrapy_cfg' or not alert:
            alert = 'Fail to deploy project, got status'
        upload_file_deploy_singlenode(filename='%s.zip' % filename, project=filename, alert=alert, fail=True)
