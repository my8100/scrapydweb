# coding: utf8
from flask import url_for

from tests.utils import PROJECT, VERSION, SPIDER, JOBID, OK, ERROR, DEFAULT_LATEST_VERSION
from tests.utils import load_json, upload_file_deploy


# def test_node_out_of_index(app, client):


# {'status': 'ok', 'pending': 0, 'running': 2, 'finished': 3}
def test_daemonstatus(app, client):
    with app.test_request_context():
        url = url_for('api', node=1, opt='daemonstatus')
        response = client.get(url)
        js = load_json(response)
        assert js['status'] == OK and 'running' in js


# def test_addversion(app, client):


# def test_schedule(app, client):


# {u'status': u'ok', u'prevstate': None, u'url': u'http://127.0.0.1:6800/cancel.json', u'status_code': 200}
def test_stop(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)

    with app.test_request_context():
        url = url_for('api', node=1, opt='stop', project=PROJECT, version_spider_job=JOBID)
        response = client.get(url)
        js = load_json(response)
        assert js['status'] == OK and 'prevstate' in js and 'times' not in js  # js['prevstate'] == 'running'


def test_forcestop(app, client):
    with app.test_request_context():
        url = url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=JOBID)
        response = client.get(url)
        js = load_json(response)
        assert js['status'] == OK and js['prevstate'] is None and js['times'] == 2


# {'status': 'ok', 'projects': ['demo']}
def test_listprojects(app, client):
    with app.test_request_context():
        url = url_for('api', node=1, opt='listprojects')
        response = client.get(url)
        js = load_json(response)
        assert js['status'] == OK and 'projects' in js


# {'status': 'ok', 'versions': []}
def test_listversions(app, client):
    with app.test_request_context():
        url = url_for('api', node=1, opt='listversions', project=PROJECT)
        response = client.get(url)
        js = load_json(response)
        assert js['status'] == OK and 'versions' in js


def listspiders(app, client, version):
    with app.test_request_context():
        url = url_for('api', node=1, opt='listspiders', project=PROJECT, version_spider_job=version)
        response = client.get(url)
        js = load_json(response)
        assert js['status'] == OK and SPIDER in js['spiders']


def test_listspiders(app, client):
    for version in [VERSION, DEFAULT_LATEST_VERSION]:
        listspiders(app, client, version)


def test_listjobs(app, client):
    with app.test_request_context():
        url = url_for('api', node=1, opt='listjobs', project=PROJECT)
        response = client.get(url)
        js = load_json(response)
        assert js['status'] == OK and 'listjobs.json' in js['url']


# "message": "[WinError 32] 另一个程序正在使用此文件，进程无法访问。: 'eggs\\\\demo\\\\2018-01-01T01_01_01.egg'",
def test_delversion(app, client):
    with app.test_request_context():
        url = url_for('api', node=1, opt='delversion', project=PROJECT, version_spider_job=VERSION)
        response = client.get(url)
        js = load_json(response)
        assert ((js['status'] == OK and 'delversion.json' in js['url']) or
                (js['status'] == ERROR and '%s.egg' % VERSION in js['message']))


# "message": "[WinError 3] 系统找不到指定的路径。: 'eggs\\\\demo'",
def test_delproject(app, client):
    with app.test_request_context():
        url = url_for('api', node=1, opt='delproject', project=PROJECT)
        response = client.get(url)
        js = load_json(response)
        assert ((js['status'] == OK and 'delproject.json' in js['url']) or
                (js['status'] == ERROR and PROJECT in js['message']))
