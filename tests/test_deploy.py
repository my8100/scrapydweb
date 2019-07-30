# coding: utf-8
from functools import partial
from io import BytesIO
import re

from tests.utils import cst, req, switch_scrapyd, upload_file_deploy


def test_deploy_from_post(app, client):
    text, __ = req(app, client, view='deploy', kws=dict(node=1), data={'1': 'on', '2': 'on'})
    assert (re.search(r'id="checkbox_1".*?checked.*?/>', text, re.S)
            and re.search(r'id="checkbox_2".*?checked.*?/>', text, re.S))


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
    nos = ['<div>demo_without_scrapy_cfg<', '<h3>NO projects found']
    req(app, client, view='deploy', kws=dict(node=2), ins=ins, nos=nos)


# {'status': 'error', 'message': 'Traceback
# ...TypeError:...activate_egg(eggpath)...\'tuple\' object is not an iterator\r\n'}
def test_addversion(app, client):
    data = {
        '1': 'on',
        'checked_amount': '1',
        'project': 'fakeproject',
        'version': 'fakeversion',
        'file': (BytesIO(b'my file contents'), "fake.egg")
    }
    req(app, client, view='deploy.upload', kws=dict(node=2), data=data, ins='activate_egg')


# <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
# <title>Redirecting...</title>
# <h1>Redirecting...</h1>
# <p>You should be redirected automatically to target URL:
# <a href="/1/schedule/demo/2018-01-01T01_01_01/">/1/schedule/demo/2018-01-01T01_01_01/</a>.  If not click the link.
def test_auto_packaging(app, client):
    data = {
        '1': 'on',
        'checked_amount': '1',
        'folder': cst.PROJECT,
        'project': cst.PROJECT,
        'version': cst.VERSION
    }
    req(app, client, view='deploy.upload', kws=dict(node=2), data=data,
        ins=['deploy results - ScrapydWeb', 'onclick="multinodeRunSpider();"', 'id="checkbox_1"'],
        nos='id="checkbox_2"')

    data.update({'2': 'on', 'checked_amount': '2'})
    req(app, client, view='deploy.upload', kws=dict(node=2), data=data,
        ins=['deploy results - ScrapydWeb', 'onclick="multinodeRunSpider();"', 'id="checkbox_1"', 'id="checkbox_2"'])


def test_auto_packaging_unicode(app, client):
    if cst.WINDOWS_NOT_CP936:
        return
    data = {
        '1': 'on',
        'checked_amount': '1',
        'folder': u'demo - 副本',
        'project': u'demo - 副本',
        'version': cst.VERSION,
    }
    req(app, client, view='deploy.upload', kws=dict(node=2), data=data, ins=['deploy results', 'demo_____'])


def test_scrapy_cfg(app, client):
    for folder, result in cst.SCRAPY_CFG_DICT.items():
        data = {
            '1': 'on',
            '2': 'on',
            'checked_amount': '2',
            'folder': folder,
            'project': cst.PROJECT,
            'version': cst.VERSION,
        }
        ins = ['fail - ScrapydWeb', result] if result else 'deploy results - ScrapydWeb'
        req(app, client, view='deploy.upload', kws=dict(node=2), data=data, ins=ins)


def test_scrapy_cfg_first_node_not_exist(app, client):
    switch_scrapyd(app)
    for folder, result in cst.SCRAPY_CFG_DICT.items():
        data = {
            '1': 'on',
            '2': 'on',
            'checked_amount': '2',
            'folder': folder,
            'project': cst.PROJECT,
            'version': cst.VERSION,
        }
        nos = []
        if folder == 'demo_only_scrapy_cfg' or not result:
            ins = ['fail - ScrapydWeb', 'the first selected node returned status']
        else:
            ins = ['fail - ScrapydWeb', result]
            nos = 'the first selected node returned status'
        req(app, client, view='deploy.upload', kws=dict(node=2), data=data, ins=ins, nos=nos)


def test_upload_file_deploy(app, client):
    upload_file_deploy_multinode = partial(upload_file_deploy, app=app, client=client, multinode=True)

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
        upload_file_deploy_multinode(filename=filename, project=project, redirect_project=redirect_project)

    for filename, alert in cst.SCRAPY_CFG_DICT.items():
        if alert:
            upload_file_deploy_multinode(filename='%s.zip' % filename, project=filename, alert=alert, fail=True)
        else:
            upload_file_deploy_multinode(filename='%s.zip' % filename, project=filename, redirect_project=filename)

    switch_scrapyd(app)

    for filename, alert in cst.SCRAPY_CFG_DICT.items():
        if filename == 'demo_only_scrapy_cfg' or not alert:
            alert = 'the first selected node returned status'
        upload_file_deploy_multinode(filename='%s.zip' % filename, project=filename, alert=alert, fail=True)


def test_deploy_xhr(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=cst.PROJECT, redirect_project=cst.PROJECT, multinode=False)
    kws = dict(
        node=1,
        eggname='%s_%s_from_file_demo.egg' % (cst.PROJECT, cst.VERSION),
        project=cst.PROJECT,
        version=cst.VERSION
    )
    req(app, client, view='deploy.xhr', kws=kws, jskws=dict(status=cst.OK, project=cst.PROJECT))
