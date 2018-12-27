# coding: utf8
import re
from io import BytesIO
from functools import partial

from tests.utils import PROJECT, VERSION, OK, WINDOWS_NOT_CP936, SCRAPY_CFG_DICT
from tests.utils import req, upload_file_deploy


def test_deploy_from_post(app, client):
    text, __ = req(app, client, view='deploy.deploy', kws=dict(node=1), data={'1': 'on', '2': 'on'})
    assert (re.search(r'id="checkbox_1".*?checked.*?/>', text, re.S)
            and re.search(r'id="checkbox_2".*?checked.*?/>', text, re.S))


def test_auto_eggifying_select_option(app, client):
    ins = [
        '(14 projects)',
        u"var folders = ['ScrapydWeb-demo', 'demo - 副本', 'demo',",
        "var projects = ['ScrapydWeb-demo', 'demo-copy', 'demo',",
        '<div>%s<' % PROJECT,
        u'<div>demo - 副本<',
        '<div>demo<',
        '<div>demo_only_scrapy_cfg<'
    ]
    nos = ['<div>demo_without_scrapy_cfg<', '<h3>NO projects found']
    req(app, client, view='deploy.deploy', kws=dict(node=2), ins=ins, nos=nos)


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
def test_auto_eggifying(app, client):
    data = {
        '1': 'on',
        'checked_amount': '1',
        'folder': PROJECT,
        'project': PROJECT,
        'version': VERSION
    }
    req(app, client, view='deploy.upload', kws=dict(node=2), data=data,
        ins=['deploy results - ScrapydWeb', 'onclick="multinodeRunSpider();"', 'id="checkbox_1"'],
        nos='id="checkbox_2"')

    data.update({'2': 'on', 'checked_amount': '2'})
    req(app, client, view='deploy.upload', kws=dict(node=2), data=data,
        ins=['deploy results - ScrapydWeb', 'onclick="multinodeRunSpider();"', 'id="checkbox_1"', 'id="checkbox_2"'])


def test_auto_eggifying_unicode(app, client):
    if WINDOWS_NOT_CP936:
        return
    data = {
        '1': 'on',
        'checked_amount': '1',
        'folder': u'demo - 副本',
        'project': u'demo - 副本',
        'version': VERSION,
    }
    req(app, client, view='deploy.upload', kws=dict(node=2), data=data, ins=['deploy results', 'demo-'])


def test_scrapy_cfg(app, client):
    for folder, result in SCRAPY_CFG_DICT.items():
        data = {
            '1': 'on',
            '2': 'on',
            'checked_amount': '2',
            'folder': folder,
            'project': PROJECT,
            'version': VERSION,
        }
        ins = ['fail - ScrapydWeb', result] if result else 'deploy results - ScrapydWeb'
        req(app, client, view='deploy.upload', kws=dict(node=2), data=data, ins=ins)


def test_scrapy_cfg_first_node_not_exist(app, client):
    app.config['SCRAPYD_SERVERS'] = app.config['SCRAPYD_SERVERS'][::-1]
    for folder, result in SCRAPY_CFG_DICT.items():
        data = {
            '1': 'on',
            '2': 'on',
            'checked_amount': '2',
            'folder': folder,
            'project': PROJECT,
            'version': VERSION,
        }
        nos = []
        if folder == 'demo_only_scrapy_cfg' or not result:
            ins = ['fail - ScrapydWeb', 'the first selected node returned status']
        else:
            ins = ['fail - ScrapydWeb', result]
            nos = 'the first selected node returned status'
        req(app, client, view='deploy.upload', kws=dict(node=2), data=data, ins=ins, nos=nos)


def test_upload_file_deploy(app, client):
    # app.config['SCRAPYD_SERVERS'] = app.config['SCRAPYD_SERVERS'][::-1]
    upload_file_deploy_multinode = partial(upload_file_deploy, app=app, client=client, multinode=True)

    filenames = ['demo.egg', 'demo_inner.zip', 'demo_outer.zip',
                 'demo - Win7CNsendzipped.zip', 'demo - Win10cp1252.zip']
    if WINDOWS_NOT_CP936:
        filenames.extend(['demo - Ubuntu.zip', 'demo - Ubuntu.tar.gz', 'demo - macOS.zip', 'demo - macOS.tar.gz'])
    else:
        filenames.extend([u'副本.zip', u'副本.tar.gz', u'副本.egg', u'demo - 副本 - Win7CN.zip',
                          u'demo - 副本 - Win7CNsendzipped.zip', u'demo - 副本 - Win10cp936.zip',
                          u'demo - 副本 - Ubuntu.zip', u'demo - 副本 - Ubuntu.tar.gz',
                          u'demo - 副本 - macOS.zip', u'demo - 副本 - macOS.tar.gz'])

    for filename in filenames:
        if filename == 'demo.egg':
            project = PROJECT
            redirect_project = PROJECT
        else:
            project = re.sub(r'\.egg|\.zip|\.tar\.gz', '', filename)
            project = 'demo_unicode' if project == u'副本' else project
            redirect_project = re.sub(r'[^0-9A-Za-z_-]', '', project)
        upload_file_deploy_multinode(filename=filename, project=project, redirect_project=redirect_project)

    for filename, alert in SCRAPY_CFG_DICT.items():
        if alert:
            upload_file_deploy_multinode(filename='%s.zip' % filename, project=filename, alert=alert, fail=True)
        else:
            upload_file_deploy_multinode(filename='%s.zip' % filename, project=filename, redirect_project=filename)

    app.config['SCRAPYD_SERVERS'] = app.config['SCRAPYD_SERVERS'][::-1]

    for filename, alert in SCRAPY_CFG_DICT.items():
        if filename == 'demo_only_scrapy_cfg' or not alert:
            alert = 'the first selected node returned status'
        upload_file_deploy_multinode(filename='%s.zip' % filename, project=filename, alert=alert, fail=True)


def test_deploy_xhr(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT, multinode=False)
    kws = dict(
        node=1,
        eggname='%s_%s_from_file_demo.egg' % (PROJECT, VERSION),
        project=PROJECT,
        version=VERSION
    )
    req(app, client, view='deploy.deploy_xhr', kws=kws, jskws=dict(status=OK, project=PROJECT))
