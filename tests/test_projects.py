# coding: utf-8
from collections import OrderedDict

from flask import url_for

from tests.utils import cst, get_text, req, upload_file_deploy


def test_listprojects(app, client):
    # upload_file_deploy(app, client, filename='demo.egg', project=cst.PROJECT, redirect_project=cst.PROJECT)
    upload_file_deploy(app, client, filename='demo.zip', project=cst.PROJECT, redirect_project=cst.PROJECT)

    req(app, client, view='projects', kws=dict(node=1), ins='Get the list of projects uploaded')


def test_listversions(app, client):
    with app.test_request_context():
        url_delproject = url_for('projects', node=1, opt='delproject', project=cst.PROJECT)
        req(app, client, view='projects', kws=dict(node=1, opt='listversions', project=cst.PROJECT),
            ins=['Delete Project', 'Delete Version', url_delproject])

        # {"status": "ok", "versions": []}
        url_delproject = url_for('projects', node=1, opt='delproject', project=cst.FAKE_PROJECT)
        req(app, client, view='projects', kws=dict(node=1, opt='listversions', project=cst.FAKE_PROJECT),
            ins=['Delete Project', url_delproject], nos='Delete the version')


# test_listspiders
# test_delversion
# test_delproject
def test_listspiders_del(app, client):
    with app.test_request_context():
        d = OrderedDict()  # For python 2 compatibility

        d['listspiders'] = dict(
            url=url_for('projects', node=1, opt='listspiders', project=cst.PROJECT, version_spider_job=cst.VERSION),
            checks=['Run Spider (test)']
        )
        d['listspiders_fail'] = dict(
            url=url_for('projects', node=1, opt='listspiders',
                        project=cst.FAKE_PROJECT, version_spider_job=cst.FAKE_VERSION),
            checks=['listspiders.json', 'No such file or directory']
        )

        d['delversion'] = dict(
            url=url_for('projects', node=1, opt='delversion', project=cst.PROJECT, version_spider_job=cst.VERSION),
            checks=['version deleted']
        )
        d['delversion_fail'] = dict(
            url=url_for('projects', node=1, opt='delversion',
                        project=cst.FAKE_PROJECT, version_spider_job=cst.FAKE_VERSION),
            checks=['delversion.json', 'See details below']
        )

        d['delproject'] = dict(
            url=url_for('projects', node=1, opt='delproject', project=cst.PROJECT),
            checks=['project deleted']
        )
        d['delproject_fail'] = dict(
            url=url_for('projects', node=1, opt='delproject', project=cst.FAKE_PROJECT),
            checks=['delproject.json', 'See details below']
        )

        for k, v in d.items():
            if k == 'delproject':  # Should use OrderedDict For python 2 compatibility
                upload_file_deploy(app, client, filename='demo.zip', project=cst.PROJECT, redirect_project=cst.PROJECT)
            response = client.get(v['url'])
            text = get_text(response)
            for c in v['checks']:
                assert c in text
