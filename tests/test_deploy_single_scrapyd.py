# coding: utf8
from io import BytesIO
from functools import partial

from flask import url_for

from tests.utils import PROJECT, VERSION, OK, WINDOWS_NOT_CP936
from tests.utils import get_text, load_json, upload_file_deploy, set_single_scrapyd


def test_auto_eggifying_select_option(app, client):
    set_single_scrapyd(app)
    with app.test_request_context():
        url = url_for('deploy.deploy', node=1)
        response = client.get(url)
        text = get_text(response)
        assert ('<option value ="%s"' % PROJECT in text
                and u'<option value ="demo"' in text
                and u'<option value ="demo - 副本"' in text
                and u'<option value ="demo_only_scrapy_cfg"' in text
                and u'<option value ="demo_without_scrapy_cfg"' not in text)


# {'status': 'error', 'message': 'Traceback
# ...TypeError:...activate_egg(eggpath)...\'tuple\' object is not an iterator\r\n'}
def test_addversion(app, client):
    set_single_scrapyd(app)
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
    set_single_scrapyd(app)
    data = {
        'project': PROJECT,
        'version': VERSION,
    }
    with app.test_request_context():
        url = url_for('deploy.upload', node=1)
        response = client.post(url, content_type='multipart/form-data', data=data)
        # http://localhost/1/schedule/ScrapydWeb-demo/2018-01-01T01_01_01/
        # app.logger.debug(response.headers['Location'])
        redirect_url = url_for('schedule.schedule', node=1, project=PROJECT, version=VERSION)
        assert response.headers['Location'].endswith(redirect_url)


def test_auto_eggifying_unicode(app, client):
    if WINDOWS_NOT_CP936:
        return
    set_single_scrapyd(app)
    data = {
        'project': u'demo - 副本',
        'version': VERSION,
    }
    with app.test_request_context():
        url = url_for('deploy.upload', node=1)
        response = client.post(url, content_type='multipart/form-data', data=data)
        assert url_for('schedule.schedule', node=1, project='demo-', version=VERSION) in get_text(response)


def test_auto_eggifying_without_scrapy_cfg(app, client):
    set_single_scrapyd(app)
    data = {
        'project': 'demo_without_scrapy_cfg',
        'version': VERSION,
    }
    with app.test_request_context():
        url = url_for('deploy.upload', node=1)
        response = client.post(url, content_type='multipart/form-data', data=data)
        assert 'scrapy.cfg NOT found' in get_text(response)


def test_auto_eggifying_only_scrapy_cfg(app, client):
    set_single_scrapyd(app)
    data = {
        'project': 'demo_only_scrapy_cfg',
        'version': VERSION,
    }
    with app.test_request_context():
        url = url_for('deploy.upload', node=1)
        response = client.post(url, content_type='multipart/form-data', data=data)
        assert 'No module named' in get_text(response)


def test_upload_file_deploy(app, client):
    set_single_scrapyd(app)
    upload_file_deploy_singlenode = partial(upload_file_deploy, app=app, client=client, multinode=False)

    upload_file_deploy_singlenode(filename='demo.egg', project=PROJECT, redirect_project=PROJECT)
    upload_file_deploy_singlenode(filename='demo - Win7CNsendzipped.zip', project='demo - Win7CNsendzipped',
                                  redirect_project='demo-Win7CNsendzipped')
    upload_file_deploy_singlenode(filename='demo - Win10cp1252.zip', project='demo - Win10cp1252',
                                  redirect_project='demo-Win10cp1252')

    if WINDOWS_NOT_CP936:
        upload_file_deploy_singlenode(filename='demo - Ubuntu.zip', project='demo - Ubuntu',
                                      redirect_project='demo-Ubuntu')
        upload_file_deploy_singlenode(filename='demo - Ubuntu.tar.gz', project='demo - Ubuntu',
                                      redirect_project='demo-Ubuntu')
        upload_file_deploy_singlenode(filename='demo - macOS.zip', project='demo - macOS',
                                      redirect_project='demo-macOS')
        upload_file_deploy_singlenode(filename='demo - macOS.tar.gz', project='demo - macOS',
                                      redirect_project='demo-macOS')
    else:
        upload_file_deploy_singlenode(filename=u'副本.zip', project='demo_zip', redirect_project='demo_zip')
        upload_file_deploy_singlenode(filename=u'副本.tar.gz', project='demo_tar_gz', redirect_project='demo_tar_gz')
        upload_file_deploy_singlenode(filename=u'副本.egg', project='demo_egg', redirect_project='demo_egg')

        upload_file_deploy_singlenode(filename=u'demo - 副本 - Win7CN.zip', project=u'demo - 副本 - Win7CN',
                                      redirect_project='demo--Win7CN')
        upload_file_deploy_singlenode(filename=u'demo - 副本 - Win7CNsendzipped.zip',
                                      project=u'demo - 副本 - Win7CNsendzipped',
                                      redirect_project='demo--Win7CNsendzipped')
        upload_file_deploy_singlenode(filename=u'demo - 副本 - Win10cp936.zip', project=u'demo - 副本 - Win10cp936',
                                      redirect_project='demo--Win10cp936')

        upload_file_deploy_singlenode(filename=u'demo - 副本 - Ubuntu.zip', project=u'demo - 副本 - Ubuntu',
                                      redirect_project='demo--Ubuntu')
        upload_file_deploy_singlenode(filename=u'demo - 副本 - Ubuntu.tar.gz', project=u'demo - 副本 - Ubuntu',
                                      redirect_project='demo--Ubuntu')
        upload_file_deploy_singlenode(filename=u'demo - 副本 - macOS.zip', project=u'demo - 副本 - macOS',
                                      redirect_project='demo--macOS')
        upload_file_deploy_singlenode(filename=u'demo - 副本 - macOS.tar.gz', project=u'demo - 副本 - macOS',
                                      redirect_project='demo--macOS')

    upload_file_deploy_singlenode(filename='demo_inner.zip', project='demo_inner', redirect_project='demo_inner')
    upload_file_deploy_singlenode(filename='demo_outer.zip', project='demo_outer', redirect_project='demo_outer')

    upload_file_deploy_singlenode(filename='demo_without_scrapy_cfg.zip', project='demo_without_scrapy_cfg',
                                  alert='scrapy.cfg NOT found', fail=True)
    upload_file_deploy_singlenode(filename='demo_only_scrapy_cfg.zip', project='demo_only_scrapy_cfg',
                                  alert='No module named', fail=True)


def test_deploy_xhr(app, client):
    set_single_scrapyd(app)
    with app.test_request_context():
        eggname = '%s_%s_from_file_demo.egg' % (PROJECT, VERSION)
        url = url_for('deploy.deploy_xhr', node=1, eggname=eggname, project=PROJECT, version=VERSION)
        response = client.post(url)
        js = load_json(response)
        assert js['status'] == OK and js['project'] == PROJECT
