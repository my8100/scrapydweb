# coding: utf-8
from tests.utils import cst, req, upload_file_deploy


# def test_node_out_of_index(app, client):


# {'status': 'ok', 'pending': 0, 'running': 2, 'finished': 3}
def test_daemonstatus(app, client):
    req(app, client, view='api', kws=dict(node=1, opt='daemonstatus'),
        jskws=dict(status=cst.OK), jskeys=['pending', 'running', 'finished'])


# def test_addversion(app, client):


# def test_schedule(app, client):


# {u'status': u'ok', u'prevstate': None, u'url': u'http://127.0.0.1:6800/cancel.json', u'status_code': 200}
# u'prevstate': running
def test_stop(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=cst.PROJECT, redirect_project=cst.PROJECT)

    req(app, client, view='api', kws=dict(node=1, opt='stop', project=cst.PROJECT, version_spider_job=cst.JOBID),
        nos='times', jskws=dict(status=cst.OK), jskeys='prevstate')


def test_forcestop(app, client):
    req(app, client, view='api', kws=dict(node=1, opt='forcestop', project=cst.PROJECT, version_spider_job=cst.JOBID),
        jskws=dict(status=cst.OK, times=2, prevstate=None))


# {'status': 'ok', 'projects': ['demo']}
def test_listprojects(app, client):
    req(app, client, view='api', kws=dict(node=1, opt='listprojects'),
        jskws=dict(status=cst.OK), jskeys='projects')


# {'status': 'ok', 'versions': []}
def test_listversions(app, client):
    req(app, client, view='api', kws=dict(node=1, opt='listversions', project=cst.PROJECT),
        jskws=dict(status=cst.OK), jskeys='versions')


def listspiders(app, client, version):
    req(app, client, view='api', kws=dict(node=1, opt='listspiders', project=cst.PROJECT, version_spider_job=version),
        jskws=dict(status=cst.OK, spiders=cst.SPIDER))


def test_listspiders(app, client):
    for version in [cst.VERSION, cst.DEFAULT_LATEST_VERSION]:
        listspiders(app, client, version)


def test_listjobs(app, client):
    req(app, client, view='api', kws=dict(node=1, opt='listjobs', project=cst.PROJECT),
        jskws=dict(status=cst.OK, url='listjobs.json'), jskeys=['pending', 'running', 'finished'])


# "message": "[WinError 32] 另一个程序正在使用此文件，进程无法访问。: 'eggs\\\\demo\\\\2018-01-01T01_01_01.egg'",
def test_delversion(app, client):
    kws = dict(node=1, opt='delversion', project=cst.PROJECT, version_spider_job=cst.VERSION)
    try:
        req(app, client, view='api', kws=kws, jskws=dict(status=cst.OK, url='delversion.json'))
    except AssertionError:
        req(app, client, view='api', kws=kws, jskws=dict(status=cst.ERROR, message='%s.egg' % cst.VERSION))


# "message": "[WinError 3] 系统找不到指定的路径。: 'eggs\\\\demo'",
def test_delproject(app, client):
    kws = dict(node=1, opt='delproject', project=cst.PROJECT)
    try:
        req(app, client, view='api', kws=kws, jskws=dict(status=cst.OK, url='delproject.json'))
    except AssertionError:
        req(app, client, view='api', kws=kws, jskws=dict(status=cst.ERROR, message=cst.PROJECT))


# After test_enable_logparser()
def test_liststats(app, client):
    # {'status': 'ok', 'details': {'pages': 'N/A', 'items': 'N/A', 'project': 'ScrapydWeb_demo', 'spider': 'N/A',
    # 'jobid': '2018-01-01T01_01_02', 'logparser_version': '0.8.0'}}
    # 'jobid': 'FAKE_JOBID'
    for jobid in [cst.JOBID, cst.FAKE_JOBID]:
        kws = dict(node=1, opt='liststats', project=cst.PROJECT, version_spider_job=jobid)
        __, js = req(app, client, view='api', kws=kws, jskeys=['status', 'details'])
        assert js['details']['project'] == cst.PROJECT
        if jobid == cst.FAKE_JOBID:
            assert js['details']['spider'] == cst.NA
        # else:
        #     assert js['details']['spider'] == cst.SPIDER
        assert js['details']['jobid'] == jobid
        assert 'pages' in js['details'] and 'items' in js['details']
        assert 'datas' not in js
