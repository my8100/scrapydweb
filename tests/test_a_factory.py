# coding: utf-8
import os

from scrapydweb import create_app
from scrapydweb.common import find_scrapydweb_settings_py
from scrapydweb.vars import SCRAPYDWEB_SETTINGS_PY
from scrapydweb.utils.check_app_config import check_app_config, check_email
from tests.utils import get_text, req
from tests.test_z_cleantest import test_cleantest as cleantest


# http://flask.pocoo.org/docs/1.0/tutorial/tests/#factory
def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_hello(client):
    response = client.get('/hello')
    assert get_text(response) == 'Hello, World!'


# def test_code_404(client):
    # response = client.get('/1/not-exist/')
    # assert response.status_code == 404 and 'Nothing Found' in get_text(response)


# How to test 500?
# def test_code_500(client):
    # response = client.get('/3/')
    # assert response.status_code == 500


def test_find_scrapydweb_settings_py():
    find_scrapydweb_settings_py(SCRAPYDWEB_SETTINGS_PY, os.getcwd())


def test_check_app_config(app, client):
    cleantest(app, client)

    # In conftest.py: ENABLE_LOGPARSER=False
    assert not os.path.exists(app.config['STATS_JSON_PATH'])

    # ['username:password@127.0.0.1:6800', ]
    app.config['SCRAPYD_SERVERS'] = app.config['_SCRAPYD_SERVERS']
    check_app_config(app.config)

    strings = []

    assert app.config['LOGPARSER_PID'] is None
    strings.append('logparser_pid: None')

    poll_pid = app.config['POLL_PID']
    if app.config.get('ENABLE_MONITOR', False):
        assert isinstance(poll_pid, int) and poll_pid > 0
    else:
        assert poll_pid is None
    strings.append('poll_pid: %s' % poll_pid)

    req(app, client, view='settings', kws=dict(node=1), ins=strings)
    assert not os.path.exists(app.config['STATS_JSON_PATH'])

    # Test ENABLE_MONITOR = False
    if app.config.get('ENABLE_MONITOR', False):
        app.config['ENABLE_MONITOR'] = False

        # ['username:password@127.0.0.1:6800', ]
        app.config['SCRAPYD_SERVERS'] = app.config['_SCRAPYD_SERVERS']
        check_app_config(app.config)

        assert app.config['LOGPARSER_PID'] is None
        assert app.config['POLL_PID'] is None
        req(app, client, view='settings', kws=dict(node=1), ins='poll_pid: None')

    # Test ENABLE_LOGPARSER = True, see test_enable_logparser()


def test_check_email_with_fake_account(app):
    with app.test_request_context():
        if not app.config.get('EMAIL_PASSWORD', ''):
            return

        app.config['EMAIL_USERNAME'] = 'username@qq.com'
        app.config['EMAIL_PASSWORD'] = 'password'
        app.config['EMAIL_SENDER'] = 'username@qq.com'
        app.config['EMAIL_RECIPIENTS'] = ['username@qq.com']
        try:
            check_email(app.config)
        except AssertionError:
            pass


def test_check_email_with_ssl_false(app):
    with app.test_request_context():
        if not app.config.get('EMAIL_PASSWORD', '') or not app.config.get('EMAIL_PASSWORD_'):
            return

        app.config['EMAIL_USERNAME'] = app.config['EMAIL_USERNAME_']
        app.config['EMAIL_PASSWORD'] = app.config['EMAIL_PASSWORD_']
        app.config['EMAIL_SENDER'] = app.config['EMAIL_SENDER_']
        app.config['EMAIL_RECIPIENTS'] = app.config['EMAIL_RECIPIENTS_']
        app.config['SMTP_SERVER'] = app.config['SMTP_SERVER_']
        app.config['SMTP_PORT'] = app.config['SMTP_PORT_']
        app.config['SMTP_OVER_SSL'] = app.config['SMTP_OVER_SSL_']
        app.config['SMTP_CONNECTION_TIMEOUT_'] = app.config['SMTP_CONNECTION_TIMEOUT_']

        check_email(app.config)


def test_scrapyd_group(app, client):
    req(app, client, view='servers', kws=dict(node=1), ins='Scrapyd-group')


def test_scrapyd_auth(app, client):
    req(app, client, view='settings', kws=dict(node=1), ins='u*e*n*m*:p*s*w*r*')  # ('username', 'password')
