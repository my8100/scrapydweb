# coding: utf8
from flask import url_for

from tests.utils import PROJECT, VERSION, SPIDER, JOBID, OK
from tests.utils import get_text, load_json, upload_file_deploy


# http://flask.pocoo.org/docs/1.0/tutorial/tests/#id11
# def test_author_required(app, client, auth):
# http://flask.pocoo.org/docs/1.0/testing/#other-testing-tricks

# {
# 'filename': 'demo_2018-01-01T01_01_01_test.pickle',
# 'cmd': 'curl http://127.0.0.1:6800/schedule.json \r\n-d project=demo \r\n
# -d _version=2018-01-01T01_01_01 \r\n-d spider=test \r\n-d jobid=2018-10-27_150842'
# }
def test_check(app, client):
    data = {
        'project': PROJECT,
        '_version': VERSION,
        'spider': SPIDER,
        'jobid': JOBID,
        'additional': "-d setting=CLOSESPIDER_TIMEOUT=10 \r\n-d setting=CLOSESPIDER_PAGECOUNT=1 \r\n-d arg1=val1",
    }
    with app.test_request_context():
        url = url_for('schedule.check', node=1)
        response = client.post(url, data=data)
        # js = response.get_json()
        js = load_json(response)
        assert js['filename'] == '%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)


# {
# "1": "on",
# "checked_amount": "1",
# "filename": "demo_2018-10-27T16_17_43_test.pickle"
# }
# <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>Redirecting...</title>\n
# <h1>Redirecting...</h1>\n<p>You should be redirected automatically to target URL:
# <a href="/1/dashboard/">/1/dashboard/</a>.  If not click the link.
def test_run(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)

    with app.test_request_context():
        url = url_for('schedule.run', node=1)
        data = {'filename': '%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER)}
        response = client.post(url, data=data)
        assert url_for('dashboard', node=1) in get_text(response)

        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=JOBID))


def test_schedule_xhr(app, client):
    with app.test_request_context():
        url = url_for('schedule.schedule_xhr', node=1, filename='%s_%s_%s.pickle' % (PROJECT, VERSION, SPIDER))
        response = client.post(url)
        js = load_json(response)
        assert js['status'] == OK and js['jobid'] == JOBID

        client.get(url_for('api', node=1, opt='forcestop', project=PROJECT, version_spider_job=JOBID))


def test_history_log(app, client):
    with app.test_request_context():
        url = url_for('schedule.history', node=1, filename='history.log')
        response = client.get(url)
        assert 'history.log' in get_text(response)
