# coding: utf8
from flask import url_for


projects = ['demo-', 'demo--macOS', 'demo--Ubuntu', 'demo--Win10cp936', 'demo--Win7CN',
            'demo--Win7CNsendzipped', 'demo-Win10cp1252', 'demo-Win7CNsendzipped',
            'demo_egg', 'demo_inner', 'demo_only_scrapy_cfg', 'demo_outer',
            'demo_tar_gz', 'demo_zip', 'fakeproject', 'ScrapydWeb-demo']


def test_cleantest(app, client):
    with app.test_request_context():
        for project in projects:
            url = url_for('api', node=1, opt='delproject', project=project)
            client.get(url)
