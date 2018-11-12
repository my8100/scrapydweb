# coding: utf8
import os

from flask import url_for

from scrapydweb import create_app
from scrapydweb.run import SCRAPYDWEB_SETTINGS_PY
from scrapydweb.utils.utils import find_scrapydweb_settings_py
from scrapydweb.utils.check_app_config import check_app_config, check_email
from scrapydweb.utils.cache import printf  # Test the import action only
from scrapydweb.utils.init_caching import init_caching
from tests.utils import get_text


# http://flask.pocoo.org/docs/1.0/tutorial/tests/#factory
def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_hello(client):
    response = client.get('/hello')
    assert get_text(response) == 'Hello, World!'


def test_find_scrapydweb_settings_py():
    find_scrapydweb_settings_py(SCRAPYDWEB_SETTINGS_PY, os.getcwd())


def test_ap_config(app):
    check_app_config(app.config)


def test_check_email_with_fake_password(app):
    with app.test_request_context():
        if app.config.get('DISABLE_EMAIL', True):
            return

        app.config['EMAIL_PASSWORD'] = 'fakepassword'

        try:
            check_email(app.config)
        except AssertionError:
            pass


def test_check_email_with_ssl_false(app):
    with app.test_request_context():
        if app.config.get('DISABLE_EMAIL', True) or not app.config.get('SMTP_SERVER_'):
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


def test_scrapyd_group_auth(app, client):
    with app.test_request_context():
        url = url_for('overview', node=1)
        response = client.get(url)
        assert ('Scrapyd-group' in get_text(response)
                and 'Scrapyd-username:Scrapyd-password' in get_text(response))
