# coding: utf8
import os

import pytest

from scrapydweb import create_app
from scrapydweb.vars import DEFAULT_LATEST_VERSION


CWD = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SCRAPYD_SERVERS': ['127.0.0.1:6800'],
        'SCRAPY_PROJECTS_DIR': os.path.join(CWD, 'data'),
    })

    @app.context_processor
    def inject_variable():
        return {
            'SCRAPYD_SERVERS': app.config['SCRAPYD_SERVERS'],
            'SCRAPYD_SERVERS_GROUPS': ['fakegroup' for s in app.config['SCRAPYD_SERVERS']],
            'SCRAPYD_SERVERS_AUTHS': [('fakeusername', 'fakepassword') for s in app.config['SCRAPYD_SERVERS']],
            'DEFAULT_LATEST_VERSION': DEFAULT_LATEST_VERSION,
            'DAEMONSTATUS_REFRESH_INTERVAL': 0,
        }

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
