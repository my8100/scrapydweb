# coding: utf8
import re

from tests.utils import PROJECT, VERSION, SPIDER, JOBID, ERROR
from tests.utils import req, upload_file_deploy


# Multinode Run Spider button in deploy results page
# Multinode Run Spider button in overview page
def test_schedule_from_post(app, client):
    text, __ = req(app, client, view='schedule.schedule', kws=dict(node=1), data={'1': 'on', '2': 'on'})
    assert (re.search(r'id="checkbox_1".*?checked.*?/>', text, re.S)
            and re.search(r'id="checkbox_2".*?checked.*?/>', text, re.S))


# CHECK first to generate xx.pickle for RUN
def test_check(app, client):
    data = {
        'project': PROJECT,
        '_version': VERSION,
        'spider': SPIDER,
        'jobid': JOBID
    }
    req(app, client, view='schedule.check', kws=dict(node=2), data=data,
        jskws=dict(filename='%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)))


# {
# "1": "on",
# "2": "on",
# "checked_amount": "2",
# "filename": "demo_2018-11-22T22_21_19_test.pickle"
# }
def test_run(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)

    data = {
        '1': 'on',
        '2': 'on',
        'checked_amount': '2',
        'filename': '%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)
    }
    req(app, client, view='schedule.run', kws=dict(node=2), data=data,
        ins=['run results - ScrapydWeb', 'id="checkbox_2"', 'onclick="passToOverview();"'])

    req(app, client, view='api', kws=dict(node=1, opt='forcestop', project=PROJECT, version_spider_job=JOBID))


def test_run_fail(app, client):
    data = {
        '1': 'on',
        '2': 'on',
        'checked_amount': '2',
        'filename': '%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)
    }
    app.config['SCRAPYD_SERVERS'] = app.config['SCRAPYD_SERVERS'][::-1]
    req(app, client, view='schedule.run', kws=dict(node=2), data=data, ins='Multinode schedule terminated')


def test_schedule_xhr(app, client):
    req(app, client, view='schedule.schedule_xhr',
        kws=dict(node=2, filename='%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)),
        jskws=dict(status=ERROR))
