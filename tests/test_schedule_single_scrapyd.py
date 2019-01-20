# coding: utf8
from flask import url_for

from tests.utils import cst, req_single_scrapyd, sleep, upload_file_deploy


# http://flask.pocoo.org/docs/1.0/tutorial/tests/#id11
# def test_author_required(app, client, auth):
# http://flask.pocoo.org/docs/1.0/testing/#other-testing-tricks


# START button of Dashboard page / Run Spider button of Logs page
# this.form.selectedProject = 'ScrapydWeb_demo';
# this.form.selectedVersion = 'default: the latest version';
# this.loadSpiders();
# this.form.selectedSpider = 'test';
def test_schedule_with_url_project(app, client):
    ins = [
        "selectedProject = '%s'" % cst.PROJECT,
        "selectedVersion = 'default: the latest version'",
        "this.loadSpiders();",
        "selectedSpider = '%s'" % cst.SPIDER
    ]
    kws = dict(node=1, project=cst.PROJECT, version=cst.DEFAULT_LATEST_VERSION, spider=cst.SPIDER)
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
# "project": "ScrapydWeb_demo",
# "_version": "default: the latest version",
# "spider": "test"
# }
def test_check(app, client):
    data = {
        'project': cst.PROJECT,
        '_version': cst.VERSION,
        'spider': cst.SPIDER,
        'jobid': cst.JOBID,
        'USER_AGENT': 'chrome',
        'COOKIES_ENABLED': 'False',
        'ROBOTSTXT_OBEY': 'False',
        'CONCURRENT_REQUESTS': '1',
        'DOWNLOAD_DELAY': '2',
        'additional': '-d setting=CLOSESPIDER_TIMEOUT=60 \r\n-d setting=CLOSESPIDER_PAGECOUNT=10 \r\n-d arg1=val1'
    }

    data_ = {
        'project': cst.PROJECT,
        '_version': cst.DEFAULT_LATEST_VERSION,
        'spider': cst.SPIDER,
        'additional': '-d setting=CLOSESPIDER_TIMEOUT=60 -d arg1'
    }
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=1), data=data,
                       jskws=dict(filename='%s_%s_%s.pickle' % (cst.PROJECT, cst.VERSION, cst.SPIDER)))
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=1), data=data_,
                       jskws=dict(filename='%s_%s_%s.pickle' % (cst.PROJECT, 'default-the-latest-version', cst.SPIDER)))


# {
# "1": "on",
# "checked_amount": "1",
# "filename": "demo_2018-10-27T16_17_43_test.pickle"
# }
# <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>Redirecting...</title>\n
# <h1>Redirecting...</h1>\n<p>You should be redirected automatically to target URL:
# <a href="/1/dashboard/">/1/dashboard/</a>.  If not click the link.
def test_run(app, client):
    # ScrapydWeb_demo.egg: custom_settings = {}, also log settings & arguments
    upload_file_deploy(app, client, filename='ScrapydWeb_demo.egg', project=cst.PROJECT, redirect_project=cst.PROJECT)

    with app.test_request_context():
        req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=1),
                           data=dict(filename='%s_%s_%s.pickle' % (cst.PROJECT, cst.VERSION, cst.SPIDER)),
                           location=url_for('dashboard', node=1))

    sleep()

    ins = [
        'JOB: %s' % cst.JOBID,
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
                       kws=dict(node=1, opt='utf8', project=cst.PROJECT, spider=cst.SPIDER, job=cst.JOBID),
                       ins=ins)
    req_single_scrapyd(app, client, view='api',
                       kws=dict(node=1, opt='forcestop', project=cst.PROJECT, version_spider_job=cst.JOBID))


def test_run_fail(app, client):
    req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=1),
                       data={'filename': '%s_%s_%s.pickle' % (cst.PROJECT, cst.VERSION, cst.SPIDER)},
                       ins='Fail to schedule', set_to_second=True)


def test_schedule_xhr(app, client):
    req_single_scrapyd(app, client, view='schedule.schedule_xhr',
                       kws=dict(node=1, filename='%s_%s_%s.pickle' % (cst.PROJECT, cst.VERSION, cst.SPIDER)),
                       jskws=dict(status=cst.OK, jobid=cst.JOBID))
    req_single_scrapyd(app, client, view='api',
                       kws=dict(node=1, opt='forcestop', project=cst.PROJECT, version_spider_job=cst.JOBID))


def test_history_log(app, client):
    req_single_scrapyd(app, client, view='schedule.history', kws=dict(filename='history.log'), ins='history.log')
