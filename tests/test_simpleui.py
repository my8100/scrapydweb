# coding: utf8
import json

from utils import simple_ui


def test_index(client):
    response = client.get('/?ui=simple')
    assert '/1/dashboard/?ui=simple' in response.headers['Location']


def test_dashboard(client):
    response = client.get('/1/dashboard/?ui=simple')
    assert b"Visit New UI" in response.data and simple_ui(response.data)


def test_items(client):
    response = client.get('/1/items/?ui=simple')
    assert ((b"Directory listing for /items/" in response.data or b"No Such Resource" in response.data)
           and simple_ui(response.data))


def test_logs(client):
    response = client.get('/1/logs/?ui=simple')
    assert b"Directory listing for /logs/" in response.data and simple_ui(response.data)


def test_log_uploaded_demo_txt(client):
    response = client.get('/1/log/uploaded/demo.txt?ui=simple')
    assert b"Stats collection" in response.data and simple_ui(response.data)


def test_log_upload(client):
    response = client.get('/1/log/upload/?ui=simple')
    assert b"Upload and parse" in response.data and simple_ui(response.data)


# { "message": "Scrapy 1.5.0 - no active project\r\n\r\n
# Unknown command: list\r\n\r\nUse \"scrapy\" to see available commands\r\n",
# "node_name": "win7-PC", "status": "error", "status_code": 200, "url": "http://127.0.0.1:6800/schedule.json" }
def test_api_start(client):
    response = client.get('/1/api/start/fakeproject/fakespider/?ui=simple')
    js = json.loads(response.data)
    assert js['status'] == 'error' and 'no active project' in js['message'] and 'times' not in js


# { "message": "'fakeproject'", "node_name": "win7-PC", "status": "error",
# "status_code": 200, "url": "http://127.0.0.1:6800/cancel.json" }
def test_api_stop(client):
    response = client.get('/1/api/stop/fakeproject/fakejob/?ui=simple')
    js = json.loads(response.data)
    assert js['status'] == 'error' and js['message'] == "'fakeproject'" and 'times' not in js


def test_api_forcestop(client):
    response = client.get('/1/api/forcestop/fakeproject/fakejob/?ui=simple')
    js = json.loads(response.data)
    assert js['status'] == 'error' and js['message'] == "'fakeproject'" and js['times'] == 2


def test_log_utf8(client):
    response = client.get('/1/log/utf8/fakeproject/fakespider/fakejob/?ui=simple')
    assert b"No Such Resource" in response.data and simple_ui(response.data)


def test_log_stats(client):
    response = client.get('/1/log/stats/fakeproject/fakespider/fakejob/?ui=simple')
    assert b"No Such Resource" in response.data and simple_ui(response.data)
