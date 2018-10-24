# coding: utf8
import logging

from flask import Flask
from flask_compress import Compress


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )
    # http://flask.pocoo.org/docs/1.0/config/#configuring-from-files
    app.config.from_object('scrapydweb.default_settings')

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from . import index, api
    from .jobs import dashboard, overview, multinode
    from .projects import deploy, schedule, manage
    from .directory import log, logs, items, parse
    from .system import settings

    app.register_blueprint(index.bp)
    app.register_blueprint(api.bp)

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(overview.bp)
    app.register_blueprint(multinode.bp)

    app.register_blueprint(deploy.bp)
    app.register_blueprint(schedule.bp)
    app.register_blueprint(manage.bp)

    app.register_blueprint(log.bp)
    app.register_blueprint(logs.bp)
    app.register_blueprint(items.bp)
    app.register_blueprint(parse.bp)
    
    app.register_blueprint(settings.bp)

    compress = Compress()
    compress.init_app(app)

    app.jinja_env.variable_start_string = '{{ '
    app.jinja_env.variable_end_string = ' }}'

    app.logger.setLevel(logging.DEBUG)

    return app
