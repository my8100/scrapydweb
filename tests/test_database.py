# coding: utf-8
import os

from scrapydweb.vars import APSCHEDULER_DATABASE_URI, DATABASE_PATH


def test_sqlalchemy_database_uri(app):
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///' + DATABASE_PATH)
    assert APSCHEDULER_DATABASE_URI.startswith(database_url)
    assert app.config['SQLALCHEMY_DATABASE_URI'].startswith(database_url)
    for value in app.config['SQLALCHEMY_BINDS'].values():
        assert value.startswith(database_url)
