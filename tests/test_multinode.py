# coding: utf8

from tests.utils import PROJECT, VERSION, JOBID
from tests.utils import req


def multinode_command(app, client, opt, title, project, version_job=None):
    data = {'1': 'on', '2': 'on'}
    req(app, client, view='multinode', kws=dict(node=1, opt=opt, project=project, version_job=version_job),
        data=data, ins=[title, 'id="checkbox_1"', 'id="checkbox_2"'])


def test_multinode_stop(app, client):
    title = 'Stop Job (%s) of Project (%s)' % (PROJECT, JOBID)
    multinode_command(app, client, 'stop', title, PROJECT, version_job=JOBID)


def test_multinode_delproject(app, client):
    title = 'Delete Project (%s)' % PROJECT
    multinode_command(app, client, 'delproject', title, PROJECT)


def test_multinode_delversion(app, client):
    title = 'Delete Version (%s) of Project (%s)' % (VERSION, PROJECT)
    multinode_command(app, client, 'delversion', title, PROJECT, version_job=VERSION)
