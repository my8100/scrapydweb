# coding: utf-8
from tests.utils import cst, req


def multinode_command(app, client, opt, title, project, version_job=None):
    data = {'1': 'on', '2': 'on'}
    req(app, client, view='multinode', kws=dict(node=1, opt=opt, project=project, version_job=version_job),
        data=data, ins=[title, 'id="checkbox_1"', 'id="checkbox_2"'])


def test_multinode_stop(app, client):
    title = 'Stop Job (%s) of Project (%s)' % (cst.PROJECT, cst.JOBID)
    multinode_command(app, client, 'stop', title, cst.PROJECT, version_job=cst.JOBID)


def test_multinode_delproject(app, client):
    title = 'Delete Project (%s)' % cst.PROJECT
    multinode_command(app, client, 'delproject', title, cst.PROJECT)


def test_multinode_delversion(app, client):
    title = 'Delete Version (%s) of Project (%s)' % (cst.VERSION, cst.PROJECT)
    multinode_command(app, client, 'delversion', title, cst.PROJECT, version_job=cst.VERSION)
