# coding: utf8
import json


# {'node_name': 'win7-PC', 'status': 'ok', 'pending': 0, 'running': 2, 'finished': 3}
def test_daemonstatus(client):
    response = client.get('/1/api/daemonstatus/')
    js = json.loads(response.data)
    assert js['status'] == 'ok' and 'running' in js


# addversion


# schedule


# {'node_name': 'win7-PC', 'status': 'error', 'message': "'fakeproject'"}
def test_cancel(client):
    response = client.get('/1/api/stop/fakeproject/fakejob/')
    js = json.loads(response.data)
    assert js['status'] == 'error' and js['message'] == "'fakeproject'" and 'times' not in js


def test_forcestop(client):
    response = client.get('/1/api/forcestop/fakeproject/fakejob/')
    js = json.loads(response.data)
    assert js['status'] == 'error' and js['message'] == "'fakeproject'" and js['times'] == 2


# {'node_name': 'win7-PC', 'status': 'ok', 'projects': ['demo']}
def test_listprojects(client):
    response = client.get('/1/api/listprojects/')
    js = json.loads(response.data)
    assert js['status'] == 'ok' and 'projects' in js


# {'node_name': 'win7-PC', 'status': 'ok', 'versions': []}
def test_listversions(client):
    response = client.get('/1/api/listversions/fakeproject/')
    js = json.loads(response.data)
    assert js['status'] == 'ok' and 'versions' in js


# {'node_name': 'win7-PC', 'status': 'error', 'message': 'Traceback (most recent call last):...
# FileNotFoundError: [Errno 2] No such file or directory: \'eggs\\\\fakeproject\\\\fakeversion.egg\'\r\n'}
def test_listspiders(client):
    response = client.get('/1/api/listspiders/fakeproject/fakeversion/')
    js = json.loads(response.data)
    assert js['status'] == 'error' and 'FileNotFoundError' in js['message']


# {'node_name': 'win7-PC', 'status': 'error', 'message': "'fakeproject'"}
def test_listjobs(client):
    response = client.get('/1/api/listjobs/fakeproject/')
    js = json.loads(response.data)
    assert js['status'] == 'error' and js['message'] == "'fakeproject'"


# {'node_name': 'win7-PC', 'status': 'error',
# 'message': "[WinError 3] 系统找不到指定的路径。: 'eggs\\\\fakeproject\\\\fakeversion.egg'"}
def test_delversion(client):
    response = client.get('/1/api/delversion/fakeproject/fakeversion/')
    js = json.loads(response.data)
    assert js['status'] == 'error' and "fakeversion.egg" in js['message']


# {'node_name': 'win7-PC', 'status': 'error', 'message': "[WinError 3] 系统找不到指定的路径。: 'eggs\\\\fakeproject'"}
def test_delproject(client):
    response = client.get('/1/api/delproject/fakeproject/')
    js = json.loads(response.data)
    assert js['status'] == 'error' and "fakeproject" in js['message']
