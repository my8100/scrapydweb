# coding: utf-8
import os
import re

from scrapydweb.vars import APSCHEDULER_DATABASE_URI, DATA_PATH, DATABASE_PATH, ROOT_DIR


def test_option_data_path(app):
    data_path = os.environ.get('DATA_PATH', '')
    if data_path and os.environ.get('TEST_ON_CIRCLECI', 'False').lower() == 'true':
        assert not os.path.isdir(os.path.join(ROOT_DIR, 'data', 'database'))
    assert os.path.isdir(os.path.join(data_path or DATA_PATH, 'database'))


def test_option_database_url(app):
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///' + DATABASE_PATH)
    assert APSCHEDULER_DATABASE_URI.startswith(database_url)
    assert app.config['SQLALCHEMY_DATABASE_URI'].startswith(database_url)
    for value in app.config['SQLALCHEMY_BINDS'].values():
        assert value.startswith(database_url)

    m = re.match(r'sqlite:///(.+)$', database_url)
    assert os.path.isdir(m.group(1) if m else DATABASE_PATH)
