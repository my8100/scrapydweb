# coding: utf-8
from flask import url_for

from tests.utils import cst, req, sleep, upload_file_deploy


jobid = ''


def test_index(app, client):
    with app.test_request_context():
        req(app, client, view='index', kws=dict(ui='mobile'),
            location=url_for('jobs', node=1, ui='mobile'))


def test_jobs(app, client):
    req(app, client, view='jobs', kws=dict(node=1, ui='mobile'),
        ins='jobs - ScrapydWeb - mobileui', mobileui=True)


def test_api_start(app, client):
    global jobid
    upload_file_deploy(app, client, filename='demo.egg', project=cst.PROJECT, redirect_project=cst.PROJECT)

    __, js = req(app, client, view='api',
                 kws=dict(node=1, opt='start', project=cst.PROJECT, version_spider_job=cst.SPIDER),
                 jskws=dict(status=cst.OK), jskeys='jobid')
    jobid = js['jobid']


# {'prevstate': running, 'status': 'ok',
# 'status_code': 200, 'url': 'http://127.0.0.1:6800/cancel.json'}
# In demo.egg: 'CONCURRENT_REQUESTS': 1, 'DOWNLOAD_DELAY': 10
def test_api_stop(app, client):
    sleep()
    req(app, client, view='api', kws=dict(node=1, opt='stop', project=cst.PROJECT, version_spider_job=jobid),
        jskws=dict(status=cst.OK, prevstate='running'), nos='times')


def test_api_forcestop(app, client):
    sleep(5)
    req(app, client, view='api', kws=dict(node=1, opt='forcestop', project=cst.PROJECT, version_spider_job=jobid),
        jskws=dict(status=cst.OK, prevstate=None, times=2))


def test_log_utf8(app, client):
    req(app, client, view='log',
        kws=dict(node=1, opt='utf8', project=cst.PROJECT, spider=cst.SPIDER, job=jobid, ui='mobile'),
        ins='PROJECT (%s)' % cst.PROJECT, mobileui=True)


def test_log_stats(app, client):
    req(app, client, view='log',
        kws=dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=jobid, ui='mobile'),
        ins='current_time', mobileui=True)
