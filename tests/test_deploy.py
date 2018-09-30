# coding: utf8
from io import BytesIO


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
