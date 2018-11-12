# coding: utf8
import os
import time
import json

from flask import url_for


CWD = os.path.dirname(os.path.abspath(__file__))
PROJECT = 'ScrapydWeb-demo'
VERSION = '2018-01-01T01_01_01'
SPIDER = 'test'
JOBID = '2018-01-01T01_01_02'

FAKE_PROJECT = 'FAKE_PROJECT'
FAKE_VERSION = 'FAKE_VERSION'
FAKE_SPIDER = 'FAKE_SPIDER'
FAKE_JOBID = 'FAKE_JOBID'

OK = 'ok'
ERROR = 'error'


def sleep(seconds=10):
    time.sleep(seconds)


def get_text(response):
    return response.get_data(as_text=True)


def load_json(response):
    return json.loads(get_text(response))


def is_simple_ui(response):
    return '<nav>' not in get_text(response)


def upload_file_deploy(app, client, filename, project, redirect_project=None, alert=None):
    data = {
        'project': project,
        'version': VERSION,
        'file': (os.path.join(CWD, u'data/%s' % filename), filename)
    }
    with app.test_request_context():
        url = url_for('deploy.upload', node=1)
        response = client.post(url, content_type='multipart/form-data', data=data)
        if redirect_project:
            assert url_for('schedule.schedule', node=1, project=redirect_project) in get_text(response)
        else:
            assert alert in get_text(response)
