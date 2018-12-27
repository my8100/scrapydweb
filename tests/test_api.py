# coding: utf8
from tests.utils import PROJECT, VERSION, SPIDER, JOBID, OK, ERROR, DEFAULT_LATEST_VERSION
from tests.utils import req, upload_file_deploy


# def test_node_out_of_index(app, client):


# {'status': 'ok', 'pending': 0, 'running': 2, 'finished': 3}
def test_daemonstatus(app, client):
    req(app, client, view='api', kws=dict(node=1, opt='daemonstatus'),
        jskws=dict(status=OK), jskeys=['pending', 'running', 'finished'])


# def test_addversion(app, client):


# def test_schedule(app, client):


# {u'status': u'ok', u'prevstate': None, u'url': u'http://127.0.0.1:6800/cancel.json', u'status_code': 200}
# u'prevstate': running
def test_stop(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)

    req(app, client, view='api', kws=dict(node=1, opt='stop', project=PROJECT, version_spider_job=JOBID),
        nos='times', jskws=dict(status=OK), jskeys='prevstate')


def test_forcestop(app, client):
    req(app, client, view='api', kws=dict(node=1, opt='forcestop', project=PROJECT, version_spider_job=JOBID),
        jskws=dict(status=OK, times=2, prevstate=None))


# {'status': 'ok', 'projects': ['demo']}
def test_listprojects(app, client):
    req(app, client, view='api', kws=dict(node=1, opt='listprojects'),
        jskws=dict(status=OK), jskeys='projects')


# {'status': 'ok', 'versions': []}
def test_listversions(app, client):
    req(app, client, view='api', kws=dict(node=1, opt='listversions', project=PROJECT),
        jskws=dict(status=OK), jskeys='versions')


def listspiders(app, client, version):
    req(app, client, view='api', kws=dict(node=1, opt='listspiders', project=PROJECT, version_spider_job=version),
        jskws=dict(status=OK, spiders=SPIDER))


def test_listspiders(app, client):
    for version in [VERSION, DEFAULT_LATEST_VERSION]:
        listspiders(app, client, version)


def test_listjobs(app, client):
    req(app, client, view='api', kws=dict(node=1, opt='listjobs', project=PROJECT),
        jskws=dict(status=OK, url='listjobs.json'), jskeys=['pending', 'running', 'finished'])


# "message": "[WinError 32] 另一个程序正在使用此文件，进程无法访问。: 'eggs\\\\demo\\\\2018-01-01T01_01_01.egg'",
def test_delversion(app, client):
    kws = dict(node=1, opt='delversion', project=PROJECT, version_spider_job=VERSION)
    try:
        req(app, client, view='api', kws=kws,
            jskws=dict(status=OK, url='delversion.json'))
    except AssertionError:
        req(app, client, view='api', kws=kws,
            jskws=dict(status=ERROR, message='%s.egg' % VERSION))


# "message": "[WinError 3] 系统找不到指定的路径。: 'eggs\\\\demo'",
def test_delproject(app, client):
    kws = dict(node=1, opt='delproject', project=PROJECT)
    try:
        req(app, client, view='api', kws=kws,
            jskws=dict(status=OK, url='delproject.json'))
    except AssertionError:
        req(app, client, view='api', kws=kws,
            jskws=dict(status=ERROR, message=PROJECT))
