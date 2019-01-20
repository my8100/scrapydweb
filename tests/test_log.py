# coding: utf8
from datetime import datetime
from io import BytesIO
import json
import os
import re
import time

from flask import url_for

from scrapydweb.utils.poll import main as poll_py_main
from tests.utils import cst, req, sleep, upload_file_deploy


def test_log_utf8_stats(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=cst.PROJECT, redirect_project=cst.PROJECT)

    with app.test_request_context():
        kws = dict(node=1, opt='start', project=cst.PROJECT, version_spider_job=cst.SPIDER)
        __, js = req(app, client, view='api', kws=kws)
        jobid = js['jobid']

        sleep()

        # the Stats page
        req(app, client, view='log', kws=dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=jobid),
            ins='Stats collection')
        # the Log page
        req(app, client, view='log', kws=dict(node=1, opt='utf8', project=cst.PROJECT, spider=cst.SPIDER, job=jobid),
            ins='log - ScrapydWeb')

        # For testing request_scrapy_log() of LogView in log.py
        app.config['SCRAPYD_LOGS_DIR'] = 'dir-not-exist'
        req(app, client, view='log', kws=dict(node=1, opt='utf8', project=cst.PROJECT, spider=cst.SPIDER, job=jobid),
            ins='log - ScrapydWeb')

        # the Dashboard page
        url_stop = url_for('api', node=1, opt='stop', project=cst.PROJECT, version_spider_job=jobid)
        req(app, client, view='dashboard', kws=dict(node=1), ins=url_stop)

        client.get(url_for('api', node=1, opt='forcestop', project=cst.PROJECT, version_spider_job=jobid))

        # /1/schedule/ScrapydWeb_demo/default:%20the%20latest%20version/test/
        url_start = url_for('schedule.schedule', node=1, project=cst.PROJECT,
                            version=cst.DEFAULT_LATEST_VERSION, spider=cst.SPIDER)
        req(app, client, view='dashboard', kws=dict(node=1), ins=url_start)


def test_log_not_exist(app, client):
    # the Stats page
    kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.FAKE_JOBID)
    ins = ['fail - ScrapydWeb', 'status_code: 404']
    req(app, client, view='log', kws=kws, ins=ins)
    # the Log page
    kws['opt'] = 'utf8'
    ins = ['fail - ScrapydWeb', 'status_code: 404']
    req(app, client, view='log', kws=kws, ins=ins)


def test_inside_the_logs_page(app, client):
    with app.test_request_context():
        for project, spider in [(cst.PROJECT, None), (cst.PROJECT, cst.SPIDER)]:
            title = 'Directory listing for /logs/%s/%s' % (project, spider or '')

            text, __ = req(app, client, view='logs', kws=dict(node=1, project=project, spider=spider), ins=title)

            if spider:
                # http://127.0.0.1:6800/logs/ScrapydWeb_demo/test/ScrapydWeb_demo.log
                scrapyd_server = app.config['SCRAPYD_SERVERS'][0]
                assert 'http://%s/logs/%s/%s/%s' % (scrapyd_server, cst.PROJECT, cst.SPIDER, cst.DEMO_LOG) in text
                assert 'http://%s/logs/%s/%s/%s' % (scrapyd_server, cst.PROJECT, cst.SPIDER, cst.DEMO_JSON) in text

                # http://127.0.0.1:5000/1/log/stats/ScrapydWeb_demo/test/ScrapydWeb_demo.json/?with_ext=True
                url_stats_of_json = url_for('log', node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER,
                                            job=cst.DEMO_JSON, with_ext='True')
                assert url_stats_of_json in text
                # http://127.0.0.1:5000/1/log/utf8/ScrapydWeb_demo/test/ScrapydWeb_demo.json/?with_ext=True
                url_utf8_of_json = url_for('log', node=1, opt='utf8', project=cst.PROJECT, spider=cst.SPIDER,
                                           job=cst.DEMO_JSON, with_ext='True')
                assert url_utf8_of_json not in text

                url_run_spider = url_for('schedule.schedule', node=1, project=cst.PROJECT,
                                         version=cst.DEFAULT_LATEST_VERSION, spider=cst.SPIDER)
                assert url_run_spider in text


# Links of Stats and Log in the Logs page
# http://127.0.0.1:5000/1/log/stats/ScrapydWeb_demo/test/ScrapydWeb_demo.log/?with_ext=True
# http://127.0.0.1:5000/1/log/utf8/ScrapydWeb_demo/test/ScrapydWeb_demo.log/?with_ext=True
# Source: http://127.0.0.1:6800/logs/ScrapydWeb_demo/test/ScrapydWeb_demo.log
def test_demo_log_with_extension(app, client):
    with app.test_request_context():
        url_utf8 = url_for('log', node=1, opt='utf8', project=cst.PROJECT, spider=cst.SPIDER,
                           job=cst.DEMO_LOG, with_ext='True')
        url_stats = url_for('log', node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER,
                            job=cst.DEMO_LOG, with_ext='True')
        scrapyd_server = app.config['SCRAPYD_SERVERS'][0]
        url_demo_log_source = 'http://%s/logs/%s/%s/%s' % (scrapyd_server, cst.PROJECT, cst.SPIDER, cst.DEMO_LOG)
        # the Stats page
        kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_LOG, with_ext='True')
        ins = ['<tr><th>elapsed</th><td>0:01:08</td></tr>', 'id="finish_reason">finished<',
               '<h4>Log</h4>', url_utf8, '<h4>Source</h4>', url_demo_log_source]
        req(app, client, view='log', kws=kws, ins=ins)
        # the Log page
        kws = dict(node=1, opt='utf8', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_LOG, with_ext='True')
        ins = ['the Stats page &gt;&gt; View log &gt;&gt; Tail', 'PROJECT (ScrapydWeb_demo), SPIDER (test)',
               '<h4>Stats</h4>', url_stats, '<h4>Source</h4>', url_demo_log_source]
        req(app, client, view='log', kws=kws, ins=ins)

        # Stats link of json file in the Logs page
        # http://127.0.0.1:5000/1/log/stats/ScrapydWeb_demo/test/ScrapydWeb_demo.json/?with_ext=True
        url_utf8_ = url_for('log', node=1, opt='utf8', project=cst.PROJECT, spider=cst.SPIDER,
                            job=cst.DEMO_JSON, with_ext='True')
        url_demo_json_source = 'http://%s/logs/%s/%s/%s' % (scrapyd_server, cst.PROJECT, cst.SPIDER, cst.DEMO_JSON)
        kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_JSON, with_ext='True')
        ins = ['<tr><th>elapsed</th><td>0:01:08</td></tr>', 'id="finish_reason">finished<']
        req(app, client, view='log', kws=kws, ins=ins,
            nos=['<h4>Log</h4>', url_utf8_, '<h4>Source</h4>', url_demo_json_source])


# Location: http://127.0.0.1:5000/log/uploaded/ttt.txt
def test_parse_upload(app, client):
    req(app, client, view='parse.upload', kws=dict(node=1),
        data={'file': (BytesIO(b''), 'empty.log')},
        location='/parse/uploaded/')

    req(app, client, view='parse.upload', kws=dict(node=1),
        data={'file': (BytesIO(b'my file contents'), 'invalid.txt')},
        location='/parse/uploaded/')

    req(app, client, view='parse.upload', kws=dict(node=1),
        data={'file': (os.path.join(cst.CWD, 'data/%s' % cst.DEMO_LOG), cst.DEMO_LOG)},
        location='/parse/uploaded/')


def test_parse_uploaded_empty_invalid_log(app, client):
    for filename in ['empty.log', 'invalid.txt']:
        req(app, client, view='parse.uploaded', kws=dict(node=1, filename=filename),
            ins=['<tr><th>job</th><td>%s</td></tr>' % filename.split('.')[0],
                 '<tr><th>first_log_time</th><td>N/A</td></tr>'])


def test_parse_uploaded_demo_log(app, client):
    # Time string extracted from logfile doesnot contains timezone info, so avoid using hard coding timestamp.
    def string_to_timestamp(string):
        datetime_obj = datetime.strptime(string, '%Y-%m-%d %H:%M:%S')
        return int(time.mktime(datetime_obj.timetuple()))
    latest_crawl_timestamp = string_to_timestamp('2018-10-23 18:28:39')
    latest_scrape_timestamp = string_to_timestamp('2018-10-23 18:28:39')
    latest_log_timestamp = string_to_timestamp('2018-10-23 18:29:42')
    ins = [
        'PROJECT (demo), SPIDER (test)',
        '<tr><th>job</th><td>2018-10-23_182826</td></tr>',
        'Stats collection', '0:01:08',
        '"green">3<',
        '"green">2<',
        'id="finish_reason">finished<',
        'id="log_critical_count">5<',
        'id="log_error_count">5<',
        'id="log_warning_count">3<',
        'id="log_redirect_count">1<',
        'id="log_retry_count">2<',
        'id="log_ignore_count">1<',
        'var latest_crawl_timestamp = %s;' % latest_crawl_timestamp,  # 1540290519
        'var latest_scrape_timestamp = %s;' % latest_scrape_timestamp,  # 1540290519
        'var latest_log_timestamp = %s;' % latest_log_timestamp  # 1540290582
    ]
    text, __ = req(app, client, view='parse.uploaded', kws=dict(node=1, filename=cst.DEMO_LOG), ins=ins)
    # const LAST_UPDATE_TIMESTAMP = 1547708035;
    assert time.time() - int(re.search(r'LAST_UPDATE_TIMESTAMP = (\d+)', text).group(1)) < 3


def test_parse_source_demo_log(app, client):
    req(app, client, view='parse.source', kws=dict(filename=cst.DEMO_LOG),
        ins=['2018-10-23 18:28:34 [scrapy.utils.log] INFO: Scrapy 1.5.0 started (bot: demo)',
             '2018-10-23 18:29:42 [scrapy.core.engine] INFO: Spider closed (finished)'])


# scrapydweb/scrapydweb/utils/sub_process.py
def test_poll_py(app):
    _bind = app.config.get('SCRAPYDWEB_BIND', '0.0.0.0')
    _bind = '127.0.0.1' if _bind == '0.0.0.0' else _bind
    args = [
        _bind,
        str(app.config.get('SCRAPYDWEB_PORT', 5000)),
        app.config.get('USERNAME', '') if app.config.get('ENABLE_AUTH', False) else '',
        app.config.get('PASSWORD', '') if app.config.get('ENABLE_AUTH', False) else '',
        json.dumps(app.config.get('SCRAPYD_SERVERS', ['127.0.0.1'])),
        json.dumps(app.config.get('SCRAPYD_SERVERS_AUTHS', [None])),
        '3',  # str(app.config.get('POLL_ROUND_INTERVAL', 300)),
        '1',  # str(app.config.get('POLL_REQUEST_INTERVAL', 10)),
        str(app.config['MAIN_PID']),
        str(app.config.get('VERBOSE', False)),
        '10'  # exit_timeout
    ]
    ignore_finished_bool_list = poll_py_main(args)
    assert ignore_finished_bool_list == [False, True]


def test_email(app, client):
    # with app.test_request_context():
    if not app.config.get('ENABLE_EMAIL', False):
        return

    def start_a_job():
        kws = dict(node=1, opt='start', project=cst.PROJECT, version_spider_job=cst.SPIDER)
        __, js = req(app, client, view='api', kws=kws)
        sleep()
        return js['jobid']

    def forcestop_a_job(job):
        req(app, client, view='api', kws=dict(node=1, opt='forcestop', project=cst.PROJECT, version_spider_job=job))

    def post_for_poll(job, job_finished=''):
        kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=job, job_finished=job_finished)
        req(app, client, view='log', kws=kws, data={}, ins='Stats collection')

    # Simulate poll post 'Finished'
    app.config['ON_JOB_FINISHED'] = True
    jobid = start_a_job()
    post_for_poll(jobid, job_finished='True')
    forcestop_a_job(jobid)

    # Simulate poll post 'ForceStopped'
    app.config['ON_JOB_FINISHED'] = False
    app.config['LOG_CRITICAL_THRESHOLD'] = 1
    app.config['LOG_CRITICAL_TRIGGER_FORCESTOP'] = True
    jobid = start_a_job()
    post_for_poll(jobid)
    forcestop_a_job(jobid)

    # Simulate poll post 'Stopped'
    app.config['LOG_CRITICAL_THRESHOLD'] = 0
    app.config['LOG_REDIRECT_THRESHOLD'] = 1
    app.config['LOG_REDIRECT_TRIGGER_STOP'] = True
    jobid = start_a_job()
    post_for_poll(jobid)
    forcestop_a_job(jobid)

    # Simulate poll post 'Triggered'
    app.config['LOG_REDIRECT_THRESHOLD'] = 0
    app.config['LOG_IGNORE_THRESHOLD'] = 1
    jobid = start_a_job()
    post_for_poll(jobid)
    forcestop_a_job(jobid)

    # Simulate poll post 'Running'
    app.config['LOG_IGNORE_THRESHOLD'] = 0
    app.config['ON_JOB_RUNNING_INTERVAL'] = 5
    jobid = start_a_job()
    post_for_poll(jobid)  # Would NOT trigger email

    sleep()
    post_for_poll(jobid)  # Would trigger email

    app.config['ON_JOB_RUNNING_INTERVAL'] = 0
    sleep()
    post_for_poll(jobid)  # Would NOT trigger email
    forcestop_a_job(jobid)
