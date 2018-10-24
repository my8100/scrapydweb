# coding: utf8
import os
from io import BytesIO


CWD = os.path.dirname(os.path.abspath(__file__))


# {'node_name': 'win7-PC', 'status': 'error', 'message': 'Traceback
# ...TypeError:...activate_egg(eggpath)...\'tuple\' object is not an iterator\r\n'}
def test_addversion(client):
    data = {
        'project': 'fakeproject_',  # avoid collision with test_api.py
        'version': 'fakeversion_',  # avoid collision with test_api.py
        'file': (BytesIO(b'my file contents'), "fake.egg")
    }
    response = client.post('/1/deploy/upload/', content_type='multipart/form-data', data=data)
    assert b'activate_egg' in response.data


def test_upload_without_scrapy_cfg(client):
    data = {
        'project': 'demo_without_scrapy_cfg',
        'version': '2018-01-01T01_01_01',
        'file': (os.path.join(CWD, 'data/demo_without_scrapy_cfg.zip'), "demo_without_scrapy_cfg.zip")
    }
    response = client.post('/1/deploy/upload/', content_type='multipart/form-data', data=data)
    assert b'scrapy.cfg NOT found' in response.data


def test_auto_eggifying_select_option(client):
    response = client.get('/1/deploy/')
    assert b'<option value ="demo"' in response.data


# <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
# <title>Redirecting...</title>
# <h1>Redirecting...</h1>
# <p>You should be redirected automatically to target URL: <a href="/1/schedule/demo/2018-01-01T01_01_01/">/1/schedule/demo/2018-01-01T01_01_01/</a>.  If not click the link.
def test_auto_eggifying(client):
    data = {
        'project': 'demo',
        'version': '2018-01-01T01_01_01',
    }
    response = client.post('/1/deploy/upload/', content_type='multipart/form-data', data=data)
    # with open(os.path.join(CWD, 'response.html'), 'wb') as f:
        # f.write(response.data)
    assert b'/1/schedule/demo/2018-01-01T01_01_01/' in response.data


def test_upload_egg(client):
    data = {
        'project': 'test_demo_egg',
        'version': '2018-01-01T01_01_01',
        'file': (os.path.join(CWD, 'data/demo.egg'), "demo.egg")
    }
    response = client.post('/1/deploy/upload/', content_type='multipart/form-data', data=data)
    assert b'/1/schedule/test_demo_egg/2018-01-01T01_01_01/' in response.data


def test_upload_zip(client):
    data = {
        'project': 'test_demo_zip',
        'version': '2018-01-01T01_01_01',
        'file': (os.path.join(CWD, 'data/demo.zip'), "demo.zip")
    }
    response = client.post('/1/deploy/upload/', content_type='multipart/form-data', data=data)
    assert b'/1/schedule/test_demo_zip/2018-01-01T01_01_01/' in response.data


def test_upload_tar(client):
    data = {
        'project': 'test_demo_tar',
        'version': '2018-01-01T01_01_01',
        'file': (os.path.join(CWD, 'data/demo.tar'), "demo.tar")
    }
    response = client.post('/1/deploy/upload/', content_type='multipart/form-data', data=data)
    assert b'/1/schedule/test_demo_tar/2018-01-01T01_01_01/' in response.data


def test_upload_tar_gz(client):
    data = {
        'project': 'test_demo_tar_gz',
        'version': '2018-01-01T01_01_01',
        'file': (os.path.join(CWD, 'data/demo.tar.gz'), "demo.tar.gz")
    }
    response = client.post('/1/deploy/upload/', content_type='multipart/form-data', data=data)
    assert b'/1/schedule/test_demo_tar_gz/2018-01-01T01_01_01/' in response.data
