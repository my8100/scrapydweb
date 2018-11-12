# coding: utf8
from flask import url_for

from tests.utils import get_text, is_simple_ui


VIEW_TITLE_MAP = {
    'overview': 'Monitor and control',
    'dashboard': 'Get the list of pending',

    'deploy.deploy': 'Add a version to a project',
    'schedule.schedule': 'Schedule a spider run',
    'manage': 'Get the list of projects uploaded',

    'logs': 'Directory listing for /logs/',
    'parse.upload': 'Upload a scrapy log file to parse',
    'settings': 'default_settings.py'
}


def test_index(client):
    response = client.get('/')
    # with open('a.html', 'wb') as f:
        # f.write(response.data)
    # with open(os.path.join(CWD, 'response.html'), 'wb') as f:
        # f.write(response.data)
    assert '/1/' in response.headers['Location']


def test_page(app, client):
    with app.test_request_context():
        for view, title in VIEW_TITLE_MAP.items():
            url = url_for(view, node=1)
            response = client.get(url)
            assert title in get_text(response) and not is_simple_ui(response)


def test_items(app, client):
    title = 'Directory listing for /items/'
    with app.test_request_context():
        url = url_for('items', node=1)
        response = client.get(url)
        assert ((title in get_text(response) or 'No Such Resource' in get_text(response))
                and not is_simple_ui(response))
