# coding: utf8
from utils import simple_ui


def test_listprojects(client):
    response = client.get('/1/manage/')
    title = b'Get the list of projects uploaded'
    assert title in response.data and not simple_ui(response.data)


# <a class="button danger" href="javascript:;"
# onclick="execXHR('/1/manage/delproject/fakeproject/', 'versions_of_fakeproject', 'Delete project \'fakeproject\' ?');"
# >DELETE Project
# </a>
def test_listversions(client):
    response = client.get('/1/manage/listversions/fakeproject/')
    assert b"DELETE Project" in response.data


# FileNotFoundError: [Errno 2] No such file or directory: 'eggs\\fakeproject\\fakeversion.egg'
def test_listspiders(client):
    response = client.get('/1/manage/listspiders/fakeproject/fakeversion/')
    assert b"FileNotFoundError" in response.data


# [WinError 3] 系统找不到指定的路径。: 'eggs\\fakeproject\\fakeversion.egg'
def test_delversion(client):
    response = client.get('/1/manage/delversion/fakeproject/fakeversion/')
    assert b"fakeversion.egg" in response.data


# project 'fakeproject': [WinError 3] 系统找不到指定的路径。: 'eggs\\fakeproject'
def test_delproject(client):
    response = client.get('/1/manage/delproject/fakeproject/')
    assert b"fakeproject" in response.data
