# coding: utf8
import os

import pytest

from scrapydweb import create_app
from scrapydweb.vars import DEFAULT_LATEST_VERSION


CWD = os.path.dirname(os.path.abspath(__file__))
# config the email_settings below if you want to test "Email Notice"
email_settings = dict(
    # DISABLE_EMAIL=False,  # Whether to execute testcases related to "Email Notice"

    # SMTP_SERVER='smtp.qq.com',
    # SMTP_PORT=465,
    # SMTP_OVER_SSL=True,
    # SMTP_CONNECTION_TIMEOUT=10,
    # FROM_ADDR='username@qq.com',
    # EMAIL_PASSWORD='password',
    # TO_ADDRS=['username@qq.com'],

    # SMTP_SERVER_='smtp.139.com',  # Used in tests/test_a_factory.py/test_check_email_with_ssl_false()
    # SMTP_PORT_=25,
    # SMTP_OVER_SSL_=False,
    # SMTP_CONNECTION_TIMEOUT_=10,
    # FROM_ADDR_='username@139.com',
    # EMAIL_PASSWORD_='password',
    # TO_ADDRS_=['username@139.com'],

    # EMAIL_WORKING_DAYS=list(range(1, 8)),
    # EMAIL_WORKING_HOURS=list(range(24)),
    # ON_JOB_FINISHED=True,
    # LOG_CRITICAL_THRESHOLD=1,
    # LOG_CRITICAL_TRIGGER_FORCESTOP=True
)


@pytest.fixture
def app():
    config = dict(
        TESTING=True,
        SCRAPYD_SERVERS=['127.0.0.1:6800'],
        SCRAPYD_SERVERS_AUTHS=[None],
        SCRAPY_PROJECTS_DIR=os.path.join(CWD, 'data'),
        SCRAPYD_LOGS_DIR=''
    )

    # For test_a_factory.py and test_email() in test_log.py
    config.update(email_settings)

    app = create_app(config)

    @app.context_processor
    def inject_variable():
        return dict(
            SCRAPYD_SERVERS=app.config['SCRAPYD_SERVERS'],
            SCRAPYD_SERVERS_GROUPS=['Scrapyd-group'] * len(app.config['SCRAPYD_SERVERS']),
            SCRAPYD_SERVERS_AUTHS=[('Scrapyd-username', 'Scrapyd-password')] * len(app.config['SCRAPYD_SERVERS']),
            DEFAULT_LATEST_VERSION=DEFAULT_LATEST_VERSION,
            DAEMONSTATUS_REFRESH_INTERVAL=0,
            SCRAPYD_SERVERS_AMOUNT=len(app.config['SCRAPYD_SERVERS'])
        )

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
