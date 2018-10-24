# coding: utf8
from utils import simple_ui


def test_index(client):
    response = client.get('/')
    assert '/1/' in response.headers['Location']


def test_overview(client):
    response = client.get('/1/overview/')
    title = b'Monitor and control'
    # with open('a.html', 'wb') as f:
        # f.write(response.data)
    assert (title in response.data
            # and b'>Overview<' not in response.data
            and not simple_ui(response.data))


def test_dashboard(client):
    response = client.get('/1/dashboard/')
    title = b'Get the list of pending'
    assert (title in response.data
            # and b'>Overview<' not in response.data
            and not simple_ui(response.data))


def test_deploy(client):
    response = client.get('/1/deploy/')
    title = b'Add a version to a project'
    assert title in response.data and not simple_ui(response.data)


def test_schedule(client):
    response = client.get('/1/schedule/')
    title = b'Schedule a spider run'
    assert title in response.data and not simple_ui(response.data)


def test_manage(client):
    response = client.get('/1/manage/')
    title = b'Get the list of projects uploaded'
    assert title in response.data and not simple_ui(response.data)


def test_items(client):
    response = client.get('/1/items/')
    title = b'Directory listing for /items/'
    assert ((title in response.data or b"No Such Resource" in response.data)
           and not simple_ui(response.data))


def test_logs(client):
    response = client.get('/1/logs/')
    title = b'Directory listing for /logs/'
    assert title in response.data and not simple_ui(response.data)


def test_parse(client):
    response = client.get('/1/log/upload/')
    title = b'Upload to parse'
    assert title in response.data and not simple_ui(response.data)


def test_settings(client):
    response = client.get('/1/settings/')
    title = b'default_settings.py'
    assert title in response.data and not simple_ui(response.data)

