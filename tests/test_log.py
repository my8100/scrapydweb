# coding: utf8
from io import BytesIO

from utils import simple_ui


def test_log_utf8(client):
    response = client.get('/1/log/utf8/fakeproject/fakespider/fakejob/')
    assert b"No Such Resource" in response.data and not simple_ui(response.data)


def test_log_stats(client):
    response = client.get('/1/log/stats/fakeproject/fakespider/fakejob/')
    assert b"No Such Resource" in response.data and not simple_ui(response.data)


def test_log_source_demo_txt(client):
    response = client.get('/log/source/demo.txt')
    assert b"scrapy.utils.log" in response.data


def test_log_uploaded_demo_txt(client):
    response = client.get('/1/log/uploaded/demo.txt')
    assert b"Stats collection" in response.data and not simple_ui(response.data)


# Location: http://127.0.0.1:5000/log/uploaded/ttt.txt
def test_log_upload(client):
    data = {
        'file': (BytesIO(b'my file contents'), "fake.log")
    }
    response = client.post('/1/log/upload/', content_type='multipart/form-data', data=data)
    assert '/log/uploaded/' in response.headers['Location']
