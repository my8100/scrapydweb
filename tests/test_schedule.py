# coding: utf8
import re
from flask import url_for

from tests.utils import PROJECT, VERSION, SPIDER, JOBID, ERROR
from tests.utils import get_text, load_json, upload_file_deploy


# Multinode Run Spider button in deploy results page
# Multinode Run Spider button in overview page
def test_schedule_from_post(app, client):
    with app.test_request_context():
        url = url_for('schedule.schedule', node=1)
        data = {'1': 'on', '2': 'on'}
        response = client.post(url, data=data)
        text = get_text(response)
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
    with app.test_request_context():
        url = url_for('schedule.check', node=2)
        response = client.post(url, data=data)
        js = load_json(response)
        assert js['filename'] == '%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)


# {
# "1": "on",
# "2": "on",
# "checked_amount": "2",
# "filename": "demo_2018-11-22T22_21_19_test.pickle"
# }
def test_run(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)

    with app.test_request_context():
        url = url_for('schedule.run', node=2)
        data = {
            '1': 'on',
            '2': 'on',
            'checked_amount': '2',
            'filename': '%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)
        }
        response = client.post(url, data=data)
        text = get_text(response)
        assert ('run results - ScrapydWeb' in text
                and 'id="checkbox_2"' in text
                and 'onclick="passToOverview();"' in text)

        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=JOBID))


def test_run_fail(app, client):
    with app.test_request_context():
        url = url_for('schedule.run', node=2)
        data = {
            '1': 'on',
            '2': 'on',
            'checked_amount': '2',
            'filename': '%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)
        }
        app.config['SCRAPYD_SERVERS'] = app.config['SCRAPYD_SERVERS'][::-1]
        response = client.post(url, data=data)
        assert 'Multinode schedule terminated' in get_text(response)


def test_schedule_xhr(app, client):
    with app.test_request_context():
        url = url_for('schedule.schedule_xhr', node=2, filename='%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER))
        response = client.post(url)
        js = load_json(response)
        assert js['status'] == ERROR
