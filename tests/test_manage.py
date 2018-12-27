# coding: utf8
from collections import OrderedDict

from flask import url_for

from tests.utils import PROJECT, VERSION, FAKE_PROJECT, FAKE_VERSION
from tests.utils import req, get_text, upload_file_deploy


def test_listprojects(app, client):
    # upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)
    upload_file_deploy(app, client, filename='demo.zip', project=PROJECT, redirect_project=PROJECT)

    req(app, client, view='manage', kws=dict(node=1), ins='Get the list of projects uploaded')


def test_listversions(app, client):
    with app.test_request_context():
        url_delproject = url_for('manage', node=1, opt='delproject', project=PROJECT)
        req(app, client, view='manage', kws=dict(node=1, opt='listversions', project=PROJECT),
            ins=['Delete Project', 'Delete Version', url_delproject])

        # {"status": "ok", "versions": []}
        url_delproject = url_for('manage', node=1, opt='delproject', project=FAKE_PROJECT)
        req(app, client, view='manage', kws=dict(node=1, opt='listversions', project=FAKE_PROJECT),
            ins=['Delete Project', url_delproject], nos='Delete the version')


# test_listspiders
# test_delversion
# test_delproject
def test_listspiders_del(app, client):
    with app.test_request_context():
        d = OrderedDict()  # For python 2 compatibility

        d['listspiders'] = dict(
            url=url_for('manage', node=1, opt='listspiders', project=PROJECT, version_spider_job=VERSION),
            checks=['Run Spider (test)']
        )
        d['listspiders_fail'] = dict(
            url=url_for('manage', node=1, opt='listspiders', project=FAKE_PROJECT, version_spider_job=FAKE_VERSION),
            checks=['listspiders.json', 'No such file or directory']
        )

        d['delversion'] = dict(
            url=url_for('manage', node=1, opt='delversion', project=PROJECT, version_spider_job=VERSION),
            checks=['version deleted']
        )
        d['delversion_fail'] = dict(
            url=url_for('manage', node=1, opt='delversion', project=FAKE_PROJECT, version_spider_job=FAKE_VERSION),
            checks=['delversion.json', 'See details below']
        )

        d['delproject'] = dict(
            url=url_for('manage', node=1, opt='delproject', project=PROJECT),
            checks=['project deleted']
        )
        d['delproject_fail'] = dict(
            url=url_for('manage', node=1, opt='delproject', project=FAKE_PROJECT),
            checks=['delproject.json', 'See details below']
        )

        for k, v in d.items():
            if k == 'delproject':  # Should use OrderedDict For python 2 compatibility
                upload_file_deploy(app, client, filename='demo.zip', project=PROJECT, redirect_project=PROJECT)
            response = client.get(v['url'])
            text = get_text(response)
            for c in v['checks']:
                assert c in text
