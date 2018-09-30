# coding: utf8
from utils import simple_ui


def test_index(client):
    response = client.get('/')
    assert '/1/' in response.headers['Location']


def test_overview(client):
    response = client.get('/1/overview/')
    title = b'Monitor and interactive with'
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


def test_directory(client):
    response = client.get('/1/directory/')
    title = b'Directory listing for'
    assert title in response.data and not simple_ui(response.data)


def test_parse(client):
    response = client.get('/1/logs/upload/')
    title = b'Upload to parse'
    assert title in response.data and not simple_ui(response.data)
