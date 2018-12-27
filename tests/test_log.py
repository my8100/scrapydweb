# coding: utf8
from io import BytesIO

from flask import url_for

from tests.utils import PROJECT, SPIDER, DEFAULT_LATEST_VERSION
from tests.utils import req, sleep, upload_file_deploy


def test_log_utf8_stats(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)

    with app.test_request_context():
        __, js = req(app, client, view='api', kws=dict(node=1, opt='start', project=PROJECT, version_spider_job=SPIDER))
        print(js)
        jobid = js['jobid']

        sleep()

        # Log page
        req(app, client, view='log', kws=dict(node=1, opt='utf8', project=PROJECT, spider=SPIDER, job=jobid),
            ins='log - ScrapydWeb')

        # Stats page
        req(app, client, view='log', kws=dict(node=1, opt='stats', project=PROJECT, spider=SPIDER, job=jobid),
            ins='Stats collection')

        # Dashboard page
        url_stop = url_for('api', node=1, opt='stop', project=PROJECT, version_spider_job=jobid)
        req(app, client, view='dashboard', kws=dict(node=1),
            ins=url_stop)

        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=jobid))

        # /1/schedule/ScrapydWeb-demo/default:%20the%20latest%20version/test/
        url_start = url_for('schedule.schedule', node=1, project=PROJECT,
                            version=DEFAULT_LATEST_VERSION, spider=SPIDER)
        req(app, client, view='dashboard', kws=dict(node=1),
            ins=url_start)


def test_logs_inside(app, client):
    with app.test_request_context():
        for project, spider in [(PROJECT, None), (PROJECT, SPIDER)]:
            title = 'Directory listing for /logs/%s/%s' % (project, spider or '')

            text, __ = req(app, client, view='logs', kws=dict(node=1, project=project, spider=spider),
                           ins=title)

            if spider:
                url_run_spider = url_for('schedule.schedule', node=1, project=PROJECT,
                                         version=DEFAULT_LATEST_VERSION, spider=SPIDER)
                assert url_run_spider in text


def test_parse_source_demo_txt(app, client):
    req(app, client, view='parse.source', kws=dict(filename='demo.txt'),
        ins='scrapy.utils.log')


def test_parse_uploaded_demo_txt(app, client):
    req(app, client, view='parse.uploaded', kws=dict(node=1, filename='demo.txt'),
        ins='Stats collection')


# Location: http://127.0.0.1:5000/log/uploaded/ttt.txt
def test_parse_upload(app, client):
    req(app, client, view='parse.upload', kws=dict(node=1),
        data={'file': (BytesIO(b'my file contents'), "fake.log")},
        location='/parse/uploaded/')

    # with app.test_request_context():
        # url = url_for('parse.upload', node=1)
        # data = {'file': (BytesIO(b'my file contents'), "fake.log")}
        # response = client.post(url, content_type='multipart/form-data', data=data)
        # assert '/parse/uploaded/' in response.headers['Location']


def test_email(app, client):
    # with app.test_request_context():
    if not app.config.get('ENABLE_EMAIL', False):
        return

    def start_a_job():
        __, js = req(app, client, view='api', kws=dict(node=1, opt='start', project=PROJECT, version_spider_job=SPIDER))
        sleep()
        return js['jobid']

    def forcestop_a_job(job):
        req(app, client, view='api', kws=dict(node=1, opt='forcestop', project=PROJECT, version_spider_job=job))

    def post_for_caching(job, job_finished=''):
        kws = dict(node=1, opt='stats', project=PROJECT, spider=SPIDER, job=job, job_finished=job_finished)
        req(app, client, view='log', kws=kws, data={}, ins='Stats collection')

    # Simulate caching post 'Finished'
    app.config['ON_JOB_FINISHED'] = True
    jobid = start_a_job()
    post_for_caching(jobid, job_finished='True')
    forcestop_a_job(jobid)

    # Simulate caching post 'ForceStopped'
    app.config['ON_JOB_FINISHED'] = False
    app.config['LOG_CRITICAL_THRESHOLD'] = 1
    app.config['LOG_CRITICAL_TRIGGER_FORCESTOP'] = True
    jobid = start_a_job()
    post_for_caching(jobid)
    forcestop_a_job(jobid)

    # Simulate caching post 'Stopped'
    app.config['LOG_CRITICAL_THRESHOLD'] = 0
    app.config['LOG_REDIRECT_THRESHOLD'] = 1
    app.config['LOG_REDIRECT_TRIGGER_STOP'] = True
    jobid = start_a_job()
    post_for_caching(jobid)
    forcestop_a_job(jobid)

    # Simulate caching post 'Triggered'
    app.config['LOG_REDIRECT_THRESHOLD'] = 0
    app.config['LOG_IGNORE_THRESHOLD'] = 1
    jobid = start_a_job()
    post_for_caching(jobid)
    forcestop_a_job(jobid)

    # Simulate caching post 'Running'
    app.config['LOG_IGNORE_THRESHOLD'] = 0
    app.config['ON_JOB_RUNNING_INTERVAL'] = 5
    jobid = start_a_job()
    post_for_caching(jobid)  # Would NOT trigger email

    sleep()
    post_for_caching(jobid)  # Would trigger email

    app.config['ON_JOB_RUNNING_INTERVAL'] = 0
    sleep()
    post_for_caching(jobid)  # Would NOT trigger email
    forcestop_a_job(jobid)
