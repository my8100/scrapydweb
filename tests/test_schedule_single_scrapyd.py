# coding: utf8
from flask import url_for

from tests.utils import PROJECT, VERSION, SPIDER, JOBID, OK, DEFAULT_LATEST_VERSION
from tests.utils import get_text, load_json, upload_file_deploy, set_single_scrapyd, sleep


# http://flask.pocoo.org/docs/1.0/tutorial/tests/#id11
# def test_author_required(app, client, auth):
# http://flask.pocoo.org/docs/1.0/testing/#other-testing-tricks


# START button of Dashboard page / Run Spider button of Logs page
# this.form.selectedProject = 'ScrapydWeb-demo';
# this.form.selectedVersion = 'default: the latest version';
# this.loadSpiders();
# this.form.selectedSpider = 'test';
def test_schedule_with_url_project(app, client):
    set_single_scrapyd(app)
    with app.test_request_context():
        url = url_for('schedule.schedule', node=1, project=PROJECT, version=DEFAULT_LATEST_VERSION, spider=SPIDER)
        response = client.get(url)
        text = get_text(response)
        assert ("selectedProject = '%s'" % PROJECT in text
                and "selectedVersion = 'default: the latest version'" in text
                and "this.loadSpiders();" in text
                and "selectedSpider = '%s'" % SPIDER in text)


# {
# "project": "demo",
# "_version": "2018-01-01T01_01_01",
# "spider": "test"
# "jobid": "2018-12-01T15_32_01",
# "USER_AGENT": "chrome",
# "COOKIES_ENABLED": "False",
# "ROBOTSTXT_OBEY": "False",
# "CONCURRENT_REQUESTS": "1",
# "DOWNLOAD_DELAY": "2",
# "additional": "-d setting=CLOSESPIDER_TIMEOUT=60 \r\n-d setting=CLOSESPIDER_PAGECOUNT=10 \r\n-d arg1=val1",
# }

# {
# "project": "ScrapydWeb-demo",
# "_version": "default: the latest version",
# "spider": "test"
# }
def test_check(app, client):
    set_single_scrapyd(app)
    data = {
        'project': PROJECT,
        '_version': VERSION,
        'spider': SPIDER,
        'jobid': JOBID,
        'USER_AGENT': 'chrome',
        'COOKIES_ENABLED': 'False',
        'ROBOTSTXT_OBEY': 'False',
        'CONCURRENT_REQUESTS': '1',
        'DOWNLOAD_DELAY': '2',
        'additional': '-d setting=CLOSESPIDER_TIMEOUT=60 \r\n-d setting=CLOSESPIDER_PAGECOUNT=10 \r\n-d arg1=val1'
    }

    data_ = {
        'project': PROJECT,
        '_version': DEFAULT_LATEST_VERSION,
        'spider': SPIDER,
        'additional': '-d setting=CLOSESPIDER_TIMEOUT=60 -d arg1'
    }
    with app.test_request_context():
        url = url_for('schedule.check', node=1)
        response = client.post(url, data=data)
        # js = response.get_json()
        js = load_json(response)
        assert js['filename'] == '%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)

        response = client.post(url, data=data_)
        js = load_json(response)
        assert js['filename'] == '%s_%s_%s.pickle' % (PROJECT, 'default-the-latest-version', SPIDER)


# {
# "1": "on",
# "checked_amount": "1",
# "filename": "demo_2018-10-27T16_17_43_test.pickle"
# }
# <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>Redirecting...</title>\n
# <h1>Redirecting...</h1>\n<p>You should be redirected automatically to target URL:
# <a href="/1/dashboard/">/1/dashboard/</a>.  If not click the link.
def test_run(app, client):
    set_single_scrapyd(app)
    # ScrapydWeb-demo.egg: custom_settings = {}, also log settings & arguments
    upload_file_deploy(app, client, filename='ScrapydWeb-demo.egg', project=PROJECT, redirect_project=PROJECT)

    with app.test_request_context():
        url = url_for('schedule.run', node=1)
        data = {'filename': '%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)}
        response = client.post(url, data=data)
        assert url_for('dashboard', node=1) in get_text(response)

        sleep()
        url = url_for('log', node=1, opt='utf8', project=PROJECT, spider=SPIDER, job=JOBID)
        response = client.get(url)
        text = get_text(response)
        assert 'JOB: %s' % JOBID in text
        assert 'USER_AGENT: Mozilla/5.0' in text
        assert 'COOKIES_ENABLED: False' in text
        assert 'ROBOTSTXT_OBEY: False' in text
        assert 'CONCURRENT_REQUESTS: 1' in text
        assert 'DOWNLOAD_DELAY: 2' in text
        assert 'CLOSESPIDER_TIMEOUT: 60' in text
        assert 'CLOSESPIDER_PAGECOUNT: 10' in text
        assert 'self.arg1: val1' in text

        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=JOBID))


def test_run_fail(app, client):
    set_single_scrapyd(app, set_second=True)
    with app.test_request_context():
        url = url_for('schedule.run', node=1)
        data = {'filename': '%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)}
        response = client.post(url, data=data)
        assert 'Fail to schedule' in get_text(response)


def test_schedule_xhr(app, client):
    set_single_scrapyd(app)
    with app.test_request_context():
        url = url_for('schedule.schedule_xhr', node=1, filename='%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER))
        response = client.post(url)
        js = load_json(response)
        assert js['status'] == OK and js['jobid'] == JOBID

        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=JOBID))


def test_history_log(app, client):
    set_single_scrapyd(app)
    with app.test_request_context():
        url = url_for('schedule.history', filename='history.log')
        response = client.get(url)
        assert 'history.log' in get_text(response)
