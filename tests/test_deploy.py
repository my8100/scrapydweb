# coding: utf8
from io import BytesIO

from flask import url_for

from tests.utils import PROJECT, VERSION, OK
from tests.utils import get_text, load_json, upload_file_deploy


def test_auto_eggifying_select_option(app, client):
    with app.test_request_context():
        url = url_for('deploy.deploy', node=1)
        response = client.get(url)
        assert ('<option value ="%s"' % PROJECT in get_text(response)
                and u'<option value ="demo - 副本"' in get_text(response))


# {'status': 'error', 'message': 'Traceback
# ...TypeError:...activate_egg(eggpath)...\'tuple\' object is not an iterator\r\n'}
def test_addversion(app, client):
    data = {
        'project': 'fakeproject',
        'version': 'fakeversion',
        'file': (BytesIO(b'my file contents'), "fake.egg")
    }
    with app.test_request_context():
        url = url_for('deploy.upload', node=1)
        response = client.post(url, content_type='multipart/form-data', data=data)
        assert 'activate_egg' in get_text(response)


# <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
# <title>Redirecting...</title>
# <h1>Redirecting...</h1>
# <p>You should be redirected automatically to target URL:
# <a href="/1/schedule/demo/2018-01-01T01_01_01/">/1/schedule/demo/2018-01-01T01_01_01/</a>.  If not click the link.
def test_auto_eggifying(app, client):
    data = {
        'project': PROJECT,
        'version': VERSION,
    }
    with app.test_request_context():
        url = url_for('deploy.upload', node=1)
        response = client.post(url, content_type='multipart/form-data', data=data)
        assert url_for('schedule.schedule', node=1, project=PROJECT) in get_text(response)


def test_auto_eggifying_unicode(app, client):
    data = {
        'project': u'demo - 副本',
        'version': VERSION,
    }
    with app.test_request_context():
        url = url_for('deploy.upload', node=1)
        response = client.post(url, content_type='multipart/form-data', data=data)
        assert url_for('schedule.schedule', node=1, project='demo-', version=VERSION) in get_text(response)


def test_upload_file_deploy(app, client):
    upload_file_deploy(app, client, filename='demo.egg', project=PROJECT, redirect_project=PROJECT)

    upload_file_deploy(app, client, filename='demo.zip', project='test_demo_zip',
                       redirect_project='test_demo_zip')
    upload_file_deploy(app, client, filename='demo_inner.zip', project='test_inner_zip',
                       redirect_project='test_inner_zip')
    upload_file_deploy(app, client, filename='demo_outer.zip', project='test_outer_zip',
                       redirect_project='test_outer_zip')
    upload_file_deploy(app, client, filename=u'demo - 副本.zip', project=u'demo - 副本', redirect_project='demo-')

    upload_file_deploy(app, client, filename='demo.tar', project='test_demo_tar', redirect_project='test_demo_tar')
    upload_file_deploy(app, client, filename=u'demo - 副本.tar', project=u'demo - 副本', redirect_project='demo-')
    upload_file_deploy(app, client, filename='demo.tar.gz', project='test_demo_tar_gz',
                       redirect_project='test_demo_tar_gz')

    upload_file_deploy(app, client, filename='demo_without_scrapy_cfg.zip', project='demo_without_scrapy_cfg',
                       alert='scrapy.cfg NOT found')
    upload_file_deploy(app, client, filename='demo_only_scrapy_cfg.zip', project='demo_only_scrapy_cfg',
                       alert='ModuleNotFoundError')


def test_deploy_xhr(app, client):
    with app.test_request_context():
        eggname = '%s_%s_from_file_demo.egg' % (PROJECT, VERSION)
        url = url_for('deploy.deploy_xhr', node=1, eggname=eggname, project=PROJECT, version=VERSION)
        response = client.post(url)
        js = load_json(response)
        assert js['status'] == OK and js['project'] == PROJECT
