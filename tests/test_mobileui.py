# coding: utf8
from flask import url_for

from tests.utils import PROJECT, SPIDER, OK
from tests.utils import req, sleep, upload_file_deploy


jobid = ''


def test_index(app, client):
    with app.test_request_context():
        req(app, client, view='index', kws=dict(ui='mobile'),
            location=url_for('dashboard', node=1, ui='mobile'))


def test_dashboard(app, client):
    req(app, client, view='dashboard', kws=dict(node=1, ui='mobile'),
        ins='dashboard - mobileui - ScrapydWeb', mobileui=True)


def test_api_start(app, client):
    global jobid
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)

    __, js = req(app, client, view='api', kws=dict(node=1, opt='start', project=PROJECT, version_spider_job=SPIDER),
                 jskws=dict(status=OK), jskeys='jobid')
    jobid = js['jobid']


# {'prevstate': running, 'status': 'ok',
# 'status_code': 200, 'url': 'http://127.0.0.1:6800/cancel.json'}
def test_api_stop(app, client):
    sleep()
    req(app, client, view='api', kws=dict(node=1, opt='stop', project=PROJECT, version_spider_job=jobid),
        jskws=dict(status=OK, prevstate='running'), nos='times')


def test_api_forcestop(app, client):
    sleep(5)
    req(app, client, view='api', kws=dict(node=1, opt='forcestop', project=PROJECT, version_spider_job=jobid),
        jskws=dict(status=OK, prevstate=None, times=2))


def test_log_utf8(app, client):
    req(app, client, view='log', kws=dict(node=1, opt='utf8', project=PROJECT, spider=SPIDER, job=jobid, ui='mobile'),
        ins='PROJECT (%s)' % PROJECT, mobileui=True)


def test_log_stats(app, client):
    req(app, client, view='log', kws=dict(node=1, opt='stats', project=PROJECT, spider=SPIDER, job=jobid, ui='mobile'),
        ins='current_time', mobileui=True)
