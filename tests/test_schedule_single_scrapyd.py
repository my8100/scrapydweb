# coding: utf8
from flask import url_for

from tests.utils import PROJECT, VERSION, SPIDER, JOBID, OK, DEFAULT_LATEST_VERSION
from tests.utils import req_single_scrapyd, upload_file_deploy, sleep


# http://flask.pocoo.org/docs/1.0/tutorial/tests/#id11
# def test_author_required(app, client, auth):
# http://flask.pocoo.org/docs/1.0/testing/#other-testing-tricks


# START button of Dashboard page / Run Spider button of Logs page
# this.form.selectedProject = 'ScrapydWeb-demo';
# this.form.selectedVersion = 'default: the latest version';
# this.loadSpiders();
# this.form.selectedSpider = 'test';
def test_schedule_with_url_project(app, client):
    ins = [
        "selectedProject = '%s'" % PROJECT,
        "selectedVersion = 'default: the latest version'",
        "this.loadSpiders();",
        "selectedSpider = '%s'" % SPIDER
    ]
    kws = dict(node=1, project=PROJECT, version=DEFAULT_LATEST_VERSION, spider=SPIDER)
    req_single_scrapyd(app, client, view='schedule.schedule', kws=kws, ins=ins)


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
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=1), data=data,
                       jskws=dict(filename='%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)))
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=1), data=data_,
                       jskws=dict(filename='%s_%s_%s.pickle' % (PROJECT, 'default-the-latest-version', SPIDER)))


# {
# "1": "on",
# "checked_amount": "1",
# "filename": "demo_2018-10-27T16_17_43_test.pickle"
# }
# <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>Redirecting...</title>\n
# <h1>Redirecting...</h1>\n<p>You should be redirected automatically to target URL:
# <a href="/1/dashboard/">/1/dashboard/</a>.  If not click the link.
def test_run(app, client):
    # ScrapydWeb-demo.egg: custom_settings = {}, also log settings & arguments
    upload_file_deploy(app, client, filename='ScrapydWeb-demo.egg', project=PROJECT, redirect_project=PROJECT)

    with app.test_request_context():
        req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=1),
                           data=dict(filename='%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)),
                           location=url_for('dashboard', node=1))

    sleep()

    ins = [
        'JOB: %s' % JOBID,
        'USER_AGENT: Mozilla/5.0',
        'COOKIES_ENABLED: False',
        'ROBOTSTXT_OBEY: False',
        'CONCURRENT_REQUESTS: 1',
        'DOWNLOAD_DELAY: 2',
        'CLOSESPIDER_TIMEOUT: 60',
        'CLOSESPIDER_PAGECOUNT: 10',
        'self.arg1: val1'
    ]
    req_single_scrapyd(app, client, view='log',
                       kws=dict(node=1, opt='utf8', project=PROJECT, spider=SPIDER, job=JOBID),
                       ins=ins)
    req_single_scrapyd(app, client, view='api',
                       kws=dict(node=1, opt='forcestop', project=PROJECT, version_spider_job=JOBID))


def test_run_fail(app, client):
    req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=1),
                       data={'filename': '%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)},
                       ins='Fail to schedule', set_to_second=True)


def test_schedule_xhr(app, client):
    req_single_scrapyd(app, client, view='schedule.schedule_xhr',
                       kws=dict(node=1, filename='%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)),
                       jskws=dict(status=OK, jobid=JOBID))
    req_single_scrapyd(app, client, view='api',
                       kws=dict(node=1, opt='forcestop', project=PROJECT, version_spider_job=JOBID))


def test_history_log(app, client):
    req_single_scrapyd(app, client, view='schedule.history', kws=dict(filename='history.log'),
                       ins='history.log')
