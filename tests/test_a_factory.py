# coding: utf8
import os


from scrapydweb import create_app
from scrapydweb.run import SCRAPYDWEB_SETTINGS_PY, check_scrapyd_connectivity
from scrapydweb.utils.utils import find_scrapydweb_settings_py
from scrapydweb.utils.check_app_config import check_app_config, check_email
from scrapydweb.utils.cache import printf  # Test the import action only
from scrapydweb.utils.init_caching import init_caching
from tests.utils import req, get_text

"""
with open('response.html', 'wb') as f:
    f.write(response.data)
"""


# http://flask.pocoo.org/docs/1.0/tutorial/tests/#factory
def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_hello(client):
    response = client.get('/hello')
    assert get_text(response) == 'Hello, World!'


def test_check_scrapyd_connectivity(app):
    SCRAPYD_SERVERS = app.config['SCRAPYD_SERVERS']
    SCRAPYD_SERVERS_GROUPS = app.config['SCRAPYD_SERVERS_GROUPS']
    SCRAPYD_SERVERS_AUTHS = app.config['SCRAPYD_SERVERS_AUTHS']
    servers = []
    for (group, ip_port, auth) in zip(SCRAPYD_SERVERS_GROUPS, SCRAPYD_SERVERS, SCRAPYD_SERVERS_AUTHS):
        ip, port = ip_port.split(':')
        servers.append((group, ip, port, auth))
    check_scrapyd_connectivity(servers)


# def test_code_404(client):
    # response = client.get('/1/not-exist/')
    # assert response.status_code == 404 and 'Nothing Found' in get_text(response)


# How to test 500?
# def test_code_500(client):
    # response = client.get('/3/')
    # assert response.status_code == 500


def test_find_scrapydweb_settings_py():
    find_scrapydweb_settings_py(SCRAPYDWEB_SETTINGS_PY, os.getcwd())


def test_app_config(app):
    check_app_config(app.config)


def test_check_email_with_fake_password(app):
    with app.test_request_context():
        if not app.config.get('ENABLE_EMAIL', False):
            return

        app.config['EMAIL_PASSWORD'] = 'fakepassword'

        try:
            check_email(app.config)
        except AssertionError:
            pass


def test_check_email_with_ssl_false(app):
    with app.test_request_context():
        if not app.config.get('ENABLE_EMAIL', False) or not app.config.get('SMTP_SERVER_'):
            return

        app.config['SMTP_SERVER'] = app.config['SMTP_SERVER_']
        app.config['SMTP_PORT'] = app.config['SMTP_PORT_']
        app.config['SMTP_OVER_SSL'] = app.config['SMTP_OVER_SSL_']
        app.config['SMTP_CONNECTION_TIMEOUT_'] = app.config['SMTP_CONNECTION_TIMEOUT_']
        app.config['FROM_ADDR'] = app.config['FROM_ADDR_']
        app.config['EMAIL_PASSWORD'] = app.config['EMAIL_PASSWORD_']
        app.config['TO_ADDRS'] = app.config['TO_ADDRS_']

        check_email(app.config)


# Test the import action only
def test_cache_py(app, client):
    printf("%s\n%s" % (app, client))


def test_init_caching(app):
    init_caching(app.config, os.getpid())


def test_scrapyd_group(app, client):
    req(app, client, view='overview', kws=dict(node=1), ins='Scrapyd-group')


def test_scrapyd_auth(app, client):
    req(app, client, view='settings', kws=dict(node=1), ins='**erna**:**sswo**')  # ('username', 'password')
