# coding: utf8
import json


# {"filename": "demo_2018-09-05T03_13_50_test.pickle",
# "cmd": "curl http://127.0.0.1:6800/schedule.json
# \r\n-d project=demo \r\n-d _version=2018-09-05T03_13_50 \r\n-d spider=test \r\n-d jobid=2018-09-27_130521"}
def test_check(client):
    response = client.post(
        '/1/schedule/check/', data={'project': 'fakeproject', '_version': 'fakeversion', 'spider': 'fakespider'}
    )

    js = json.loads(response.data)
    assert 'filename' in js


# test_run


def test_history_log(client):
    response = client.get('/schedule/history.log')
    assert b"history.log" in response.data
