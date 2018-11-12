# coding: utf8
from io import BytesIO

from flask import url_for

from tests.utils import PROJECT, SPIDER
from tests.utils import sleep, get_text, load_json, is_simple_ui, upload_file_deploy


def test_log_utf8_stats(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)

    with app.test_request_context():
        url = url_for('api', node=1, opt='start', project=PROJECT, version_spider_job=SPIDER)
        response = client.get(url)
        js = load_json(response)
        jobid = js['jobid']

        sleep()

        # UTF8 page
        url = url_for('log', node=1, opt='utf8', project=PROJECT, spider=SPIDER, job=jobid)
        response = client.get(url)
        assert 'utf8 - ScrapydWeb' in get_text(response) and not is_simple_ui(response)

        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=jobid))

        # Stats page
        url = url_for('log', node=1, opt='stats', project=PROJECT, spider=SPIDER, job=jobid)
        response = client.get(url)
        assert 'Stats collection' in get_text(response) and not is_simple_ui(response)


def test_logs_inside(app, client):
    with app.test_request_context():
        for project, spider in [(PROJECT, None), (PROJECT, SPIDER)]:
            title = 'Directory listing for /logs/%s/%s' % (project, spider or '')
            url = url_for('logs', node=1, project=project, spider=spider)
            response = client.get(url)
            assert title in get_text(response) and not is_simple_ui(response)


def test_parse_source_demo_txt(app, client):
    with app.test_request_context():
        url = url_for('parse.source', filename='demo.txt')
        response = client.get(url)
        assert 'scrapy.utils.log' in get_text(response)


def test_parse_uploaded_demo_txt(app, client):
    with app.test_request_context():
        url = url_for('parse.uploaded', node=1, filename='demo.txt')
        response = client.get(url)
        assert 'Stats collection' in get_text(response) and not is_simple_ui(response)


# Location: http://127.0.0.1:5000/log/uploaded/ttt.txt
def test_parse_upload(app, client):
    with app.test_request_context():
        url = url_for('parse.upload', node=1)
        data = {'file': (BytesIO(b'my file contents'), "fake.log")}
        response = client.post(url, content_type='multipart/form-data', data=data)
        assert '/parse/uploaded/' in response.headers['Location']


def test_email(app, client):
    with app.test_request_context():
        if app.config.get('DISABLE_EMAIL', True):
            return

        # Simulate caching post 'Finished'
        url = url_for('api', node=1, opt='start', project=PROJECT, version_spider_job=SPIDER)
        response = client.get(url)
        js = load_json(response)
        jobid = js['jobid']

        sleep()
        url = url_for('log', node=1, opt='stats', project=PROJECT,
                      spider=SPIDER, job=jobid, job_finished='True')
        response = client.post(url, content_type='multipart/form-data')
        assert 'Stats collection' in get_text(response)
        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=jobid))

        # Simulate caching post 'ForceStopped'
        app.config['ON_JOB_FINISHED'] = False
        url = url_for('api', node=1, opt='start', project=PROJECT, version_spider_job=SPIDER)
        response = client.get(url)
        js = load_json(response)
        jobid = js['jobid']

        sleep()
        url = url_for('log', node=1, opt='stats', project=PROJECT,
                      spider=SPIDER, job=jobid)
        response = client.post(url, content_type='multipart/form-data')
        assert 'Stats collection' in get_text(response)
        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=jobid))

        # Simulate caching post 'Stopped'
        app.config['LOG_CRITICAL_THRESHOLD'] = 0
        app.config['LOG_REDIRECT_THRESHOLD'] = 1
        app.config['LOG_REDIRECT_TRIGGER_STOP'] = True
        url = url_for('api', node=1, opt='start', project=PROJECT, version_spider_job=SPIDER)
        response = client.get(url)
        js = load_json(response)
        jobid = js['jobid']

        sleep()
        url = url_for('log', node=1, opt='stats', project=PROJECT,
                      spider=SPIDER, job=jobid)
        response = client.post(url, content_type='multipart/form-data')
        assert 'Stats collection' in get_text(response)
        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=jobid))

        # Simulate caching post 'Triggered'
        app.config['LOG_REDIRECT_THRESHOLD'] = 0
        app.config['LOG_IGNORE_THRESHOLD'] = 1

        url = url_for('api', node=1, opt='start', project=PROJECT, version_spider_job=SPIDER)
        response = client.get(url)
        js = load_json(response)
        jobid = js['jobid']

        sleep()
        url = url_for('log', node=1, opt='stats', project=PROJECT,
                      spider=SPIDER, job=jobid)
        response = client.post(url, content_type='multipart/form-data')
        assert 'Stats collection' in get_text(response)
        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=jobid))

        # Simulate caching post 'Running'
        app.config['LOG_IGNORE_THRESHOLD'] = 0
        app.config['ON_JOB_RUNNING_INTERVAL'] = 5

        url = url_for('api', node=1, opt='start', project=PROJECT, version_spider_job=SPIDER)
        response = client.get(url)
        js = load_json(response)
        jobid = js['jobid']

        # Would NOT trigger email
        sleep()
        url = url_for('log', node=1, opt='stats', project=PROJECT, spider=SPIDER, job=jobid)
        response = client.post(url, content_type='multipart/form-data')
        assert 'Stats collection' in get_text(response)

        # Would trigger email
        sleep()
        url = url_for('log', node=1, opt='stats', project=PROJECT, spider=SPIDER, job=jobid)
        response = client.post(url, content_type='multipart/form-data')
        assert 'Stats collection' in get_text(response)

        # Would NOT trigger email
        app.config['ON_JOB_RUNNING_INTERVAL'] = 0
        sleep()
        url = url_for('log', node=1, opt='stats', project=PROJECT, spider=SPIDER, job=jobid)
        response = client.post(url, content_type='multipart/form-data')
        assert 'Stats collection' in get_text(response)
        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=jobid))
