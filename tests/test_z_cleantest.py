# coding: utf8
from flask import url_for


projects = ['ScrapydWeb-demo', 'demo-', 'demo_only_scrapy_cfg', 'fakeproject',
            'test_demo_egg', 'test_demo_tar', 'test_demo_tar_gz',
            'test_demo_zip', 'test_inner_zip', 'test_outer_zip']


def test_cleantest(app, client):
    with app.test_request_context():
        for project in projects:
            url = url_for('api', node=1, opt='delproject', project=project)
            client.get(url)
