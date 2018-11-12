# coding: utf8
from flask import url_for

from tests.utils import PROJECT, SPIDER, OK
from tests.utils import sleep, get_text, load_json, is_simple_ui, upload_file_deploy


jobid = ''


def test_index(client):
    response = client.get('/?ui=simple')
    assert '/1/dashboard/?ui=simple' in response.headers['Location']


def test_dashboard(app, client):
    with app.test_request_context():
        url = url_for('dashboard', node=1, ui='simple')
        response = client.get(url)
        assert 'Visit desktop version' in get_text(response) and is_simple_ui(response)


def test_items(app, client):
    title = 'Directory listing for /items/'
    with app.test_request_context():
        url = url_for('items', node=1, ui='simple')
        response = client.get(url)
        assert ((title in get_text(response) or 'No Such Resource' in get_text(response)) and is_simple_ui(response))


def test_logs(app, client):
    title = 'Directory listing for /logs/'
    with app.test_request_context():
        url = url_for('logs', node=1, ui='simple')
        response = client.get(url)
        assert title in get_text(response) and is_simple_ui(response)


def test_parse_uploaded_demo_txt(app, client):
    with app.test_request_context():
        url = url_for('parse.uploaded', node=1, filename='demo.txt', ui='simple')
        response = client.get(url)
        assert 'Stats collection' in get_text(response) and is_simple_ui(response)


def test_parse_upload(app, client):
    title = 'Upload a scrapy log file to parse'
    with app.test_request_context():
        url = url_for('parse.upload', node=1, ui='simple')
        response = client.get(url)
        assert title in get_text(response) and is_simple_ui(response)


def test_api_start(app, client):
    global jobid
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)

    with app.test_request_context():
        url = url_for('api', node=1, opt='start', project=PROJECT, version_spider_job=SPIDER, ui='simple')
        response = client.get(url)
        js = load_json(response)
        jobid = js['jobid']
        assert js['status'] == OK and js['jobid']


# {'prevstate': running, 'status': 'ok',
# 'status_code': 200, 'url': 'http://127.0.0.1:6800/cancel.json'}
def test_api_stop(app, client):
    sleep()

    with app.test_request_context():
        url = url_for('api', node=1, opt='stop', project=PROJECT, version_spider_job=jobid, ui='simple')
        response = client.get(url)
        js = load_json(response)
        assert js['status'] == OK and js['prevstate'] == 'running' and 'times' not in js


def test_api_forcestop(app, client):
    with app.test_request_context():
        url = url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=jobid, ui='simple')
        response = client.get(url)
        js = load_json(response)
        assert js['status'] == OK and js['prevstate'] is None and js['times'] == 2


def test_log_utf8(app, client):
    with app.test_request_context():
        url = url_for('log', node=1, opt='utf8', project=PROJECT, spider=SPIDER, job=jobid, ui='simple')
        response = client.get(url)
        assert 'utf8 - ScrapydWeb' in get_text(response) and is_simple_ui(response)


def test_log_stats(app, client):
    with app.test_request_context():
        url = url_for('log', node=1, opt='stats', project=PROJECT, spider=SPIDER, job=jobid, ui='simple')
        response = client.get(url)
        assert 'Stats collection' in get_text(response) and is_simple_ui(response)
