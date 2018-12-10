# coding: utf8
from flask import url_for

from tests.utils import PROJECT, VERSION, JOBID
from tests.utils import get_text


def multinode_command(app, client, opt, title, project, version_job=None):
    with app.test_request_context():
        url = url_for('multinode', node=1, opt=opt, project=project, version_job=version_job)
        data = {'1': 'on', '2': 'on'}
        response = client.post(url, content_type='multipart/form-data', data=data)
        text = get_text(response)
        assert (title in text
                and 'id="checkbox_1"' in text
                and 'id="checkbox_2"' in text)


def test_multinode_stop(app, client):
    title = 'Stop Job (%s) of Project (%s)' % (PROJECT, JOBID)
    multinode_command(app, client, 'stop', title, PROJECT, version_job=JOBID)


def test_multinode_delproject(app, client):
    title = 'Delete Project (%s)' % PROJECT
    multinode_command(app, client, 'delproject', title, PROJECT)


def test_multinode_delversion(app, client):
    title = 'Delete Version (%s) of Project (%s)' % (VERSION, PROJECT)
    multinode_command(app, client, 'delversion', title, PROJECT, version_job=VERSION)
