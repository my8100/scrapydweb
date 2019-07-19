# coding: utf-8
import os

import pytest

from scrapydweb import create_app
from tests.utils import cst, setup_env


# Win10 Python2 Scrapyd error: environment can only contain strings
# https://github.com/scrapy/scrapyd/issues/231


# MUST be updated: _SCRAPYD_SERVER and _SCRAPYD_SERVER_AUTH
custom_settings = dict(
    _SCRAPYD_SERVER='127.0.0.1:6800',
    _SCRAPYD_SERVER_AUTH=('admin', '12345'),  # Or None

    SCRAPYD_LOGS_DIR='',  # For LogParser, defaults to the 'logs' directory that resides in current user directory

    ENABLE_EMAIL=os.environ.get('ENABLE_EMAIL', 'False') == 'True',  # Whether to execute testcases related to "Email Notice"

    SMTP_SERVER='smtp.qq.com',
    SMTP_PORT=465,
    SMTP_OVER_SSL=True,
    SMTP_CONNECTION_TIMEOUT=30,
    EMAIL_USERNAME=os.environ.get('EMAIL_USERNAME', 'username@qq.com'),
    EMAIL_PASSWORD=os.environ.get('EMAIL_PASSWORD', 'password'),
    FROM_ADDR=os.environ.get('FROM_ADDR', 'username@qq.com'),
    TO_ADDRS=[os.environ.get('TO_ADDRS', 'username@qq.com')],

    SMTP_SERVER_=os.environ.get('SMTP_SERVER_', ''),  # Used in test_check_email_with_ssl_false(), e.g. smtp.139.com
    SMTP_PORT_=25,
    SMTP_OVER_SSL_=False,
    SMTP_CONNECTION_TIMEOUT_=10,
    EMAIL_USERNAME_=os.environ.get('EMAIL_USERNAME_', 'username@139.com'),
    EMAIL_PASSWORD_=os.environ.get('EMAIL_PASSWORD_', 'password'),
    FROM_ADDR_=os.environ.get('FROM_ADDR_', 'username@139.com'),
    TO_ADDRS_=[os.environ.get('TO_ADDRS_', 'username@139.com')]
)


setup_env(custom_settings)


@pytest.fixture
def app():
    fake_server = 'scrapydweb-fake-domain.com:443'
    SCRAPYD_SERVERS = [custom_settings['_SCRAPYD_SERVER'], fake_server]
    if custom_settings['_SCRAPYD_SERVER_AUTH']:
        username, password = custom_settings['_SCRAPYD_SERVER_AUTH']
        authed_server = '%s:%s@%s' % (username, password, custom_settings['_SCRAPYD_SERVER'])
        _SCRAPYD_SERVERS = [authed_server, fake_server]
    else:
        _SCRAPYD_SERVERS = SCRAPYD_SERVERS

    config = dict(
        TESTING=True,
        # SERVER_NAME='127.0.0.1:5000',  # http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values

        DEFAULT_SETTINGS_PY_PATH='',
        SCRAPYDWEB_SETTINGS_PY_PATH='',
        MAIN_PID=os.getpid(),
        LOGPARSER_PID=0,
        POLL_PID=0,

        SCRAPYD_SERVERS=SCRAPYD_SERVERS,
        _SCRAPYD_SERVERS=_SCRAPYD_SERVERS,
        LOCAL_SCRAPYD_SERVER=custom_settings['_SCRAPYD_SERVER'],
        SCRAPYD_SERVERS_AUTHS=[custom_settings['_SCRAPYD_SERVER_AUTH'], ('username', 'password')],
        SCRAPYD_SERVERS_GROUPS=['', 'Scrapyd-group'],
        SCRAPY_PROJECTS_DIR=os.path.join(cst.ROOT_DIR, 'data'),

        ENABLE_LOGPARSER=False,

        EMAIL_WORKING_DAYS=list(range(1, 8)),
        EMAIL_WORKING_HOURS=list(range(24)),
        VERBOSE=True
    )

    config.update(custom_settings)

    app = create_app(config)

    @app.context_processor
    def inject_variable():
        return dict(
            SCRAPYD_SERVERS=app.config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800'],
            SCRAPYD_SERVERS_AMOUNT=len(app.config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800']),
            SCRAPYD_SERVERS_GROUPS=app.config.get('SCRAPYD_SERVERS_GROUPS', []) or [''],
            SCRAPYD_SERVERS_AUTHS=app.config.get('SCRAPYD_SERVERS_AUTHS', []) or [None],

            DAEMONSTATUS_REFRESH_INTERVAL=app.config.get('DAEMONSTATUS_REFRESH_INTERVAL', 10),
            ENABLE_AUTH=app.config.get('ENABLE_AUTH', False),
            SHOW_SCRAPYD_ITEMS=app.config.get('SHOW_SCRAPYD_ITEMS', True),
        )

    yield app


# https://stackoverflow.com/questions/41065584/using-url-for-in-tests
# TODO: follow_redirects=True
@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
