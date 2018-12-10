# coding: utf8
from flask import url_for

from tests.utils import PROJECT, SPIDER, OK
from tests.utils import sleep, get_text, load_json, is_mobileui, upload_file_deploy


jobid = ''


def test_index(client):
    response = client.get('/?ui=mobile')
    assert '/1/dashboard/?ui=mobile' in response.headers['Location']


def test_dashboard(app, client):
    with app.test_request_context():
        url = url_for('dashboard', node=1, ui='mobile')
        response = client.get(url)
        assert 'dashboard - mobileui - ScrapydWeb' in get_text(response) and is_mobileui(response)


def test_api_start(app, client):
    global jobid
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)

    with app.test_request_context():
        url = url_for('api', node=1, opt='start', project=PROJECT, version_spider_job=SPIDER, ui='mobile')
        response = client.get(url)
        js = load_json(response)
        jobid = js['jobid']
        assert js['status'] == OK and js['jobid']


# {'prevstate': running, 'status': 'ok',
# 'status_code': 200, 'url': 'http://127.0.0.1:6800/cancel.json'}
def test_api_stop(app, client):
    sleep()

    with app.test_request_context():
        url = url_for('api', node=1, opt='stop', project=PROJECT, version_spider_job=jobid, ui='mobile')
        response = client.get(url)
        js = load_json(response)
        assert js['status'] == OK and js['prevstate'] == 'running' and 'times' not in js


def test_api_forcestop(app, client):
    sleep(5)
    with app.test_request_context():
        url = url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=jobid, ui='mobile')
        response = client.get(url)
        js = load_json(response)
        assert js['status'] == OK and js['prevstate'] is None and js['times'] == 2


def test_log_utf8(app, client):
    with app.test_request_context():
        url = url_for('log', node=1, opt='utf8', project=PROJECT, spider=SPIDER, job=jobid, ui='mobile')
        response = client.get(url)
        assert 'PROJECT (%s)' % PROJECT in get_text(response) and is_mobileui(response)


def test_log_stats(app, client):
    with app.test_request_context():
        url = url_for('log', node=1, opt='stats', project=PROJECT, spider=SPIDER, job=jobid, ui='mobile')
        response = client.get(url)
        assert 'current_time' in get_text(response) and is_mobileui(response)
