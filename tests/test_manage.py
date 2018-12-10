# coding: utf8
from collections import OrderedDict

from flask import url_for

from tests.utils import PROJECT, VERSION, FAKE_PROJECT, FAKE_VERSION
from tests.utils import get_text, is_mobileui, upload_file_deploy


def test_listprojects(app, client):
    # upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)
    upload_file_deploy(app, client, filename='demo.zip', project=PROJECT, redirect_project=PROJECT)

    title = 'Get the list of projects uploaded'
    with app.test_request_context():
        url = url_for('manage', node=1)
        response = client.get(url)
        assert title in get_text(response) and not is_mobileui(response)


def test_listversions(app, client):
    with app.test_request_context():
        url = url_for('manage', node=1, opt='listversions', project=PROJECT)
        response = client.get(url)
        text = get_text(response)
        assert ('Delete Project' in text
                and 'Delete Version' in text
                and url_for('manage', node=1, opt='delproject', project=PROJECT) in text)

        # {"status": "ok", "versions": []}
        fake_url = url_for('manage', node=1, opt='listversions', project=FAKE_PROJECT)
        response = client.get(fake_url)
        text = get_text(response)
        assert ('Delete Project' in text
                and 'Delete the version' not in text
                and url_for('manage', node=1, opt='delproject', project=FAKE_PROJECT) in text)


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
            checks=['deleted']
        )
        d['delversion_fail'] = dict(
            url=url_for('manage', node=1, opt='delversion', project=FAKE_PROJECT, version_spider_job=FAKE_VERSION),
            checks=['delversion.json', 'See details below']
        )

        d['delproject'] = dict(
            url=url_for('manage', node=1, opt='delproject', project=PROJECT),
            checks=['deleted']
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
