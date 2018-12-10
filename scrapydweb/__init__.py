# coding: utf8
import re
import traceback
import logging
from logging.config import dictConfig

from flask import Flask
from flask_compress import Compress


title_error_500 = """
<h1>Internal Server Error</h1>
<p>The server encountered an internal error and was unable to complete your request.
Either the server is overloaded or there is an error in the application.</p>
"""

# http://flask.pocoo.org/docs/1.0/logging/#basic-configuration
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(name)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


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

    # @app.errorhandler(404)
    # def handle_error(error):
        # return ('Nothing Found', 404)

    @app.errorhandler(500)
    def handle_error(error):
        return '{}<h2>error: {}</h2><pre>{}<pre>'.format(title_error_500, error, traceback.format_exc()), 500

    handle_route(app)

    compress = Compress()
    compress.init_app(app)

    app.jinja_env.variable_start_string = '{{ '
    app.jinja_env.variable_end_string = ' }}'

    # https://ansible-docs.readthedocs.io/zh/stable-2.0/rst/playbooks_filters.html#other-useful-filters
    # https://stackoverflow.com/questions/12791216/how-do-i-use-regular-expressions-in-jinja2
    # https://www.michaelcho.me/article/custom-jinja-template-filters-in-flask
    # http://flask.pocoo.org/docs/1.0/api/#flask.Flask.template_filter
    @app.template_filter()
    def regex_replace(s, find, replace):
        return re.sub(find, replace, s)

    app.logger.setLevel(logging.DEBUG)

    return app


def handle_route(app):
    def register_view(view, endpoint, url_defaults_list):
        view_func = view.as_view(endpoint)
        for url, defaults in url_defaults_list:
            app.add_url_rule('/<int:node>/%s/' % url, defaults=defaults, view_func=view_func)

    from .index import IndexView
    index_view = IndexView.as_view('index')
    app.add_url_rule('/<int:node>/', view_func=index_view)
    app.add_url_rule('/', defaults=dict(node=1), view_func=index_view)

    from .api import ApiView
    register_view(ApiView, 'api', [
        ('api/<opt>/<project>/<version_spider_job>', None),
        ('api/<opt>/<project>', dict(version_spider_job=None)),
        ('api/<opt>', dict(project=None, version_spider_job=None))
    ])

    # jobs
    from .jobs.dashboard import DashboardView
    register_view(DashboardView, 'dashboard', [('dashboard', None)])

    from .jobs.overview import OverviewView
    register_view(OverviewView, 'overview', [
        ('overview/<opt>/<project>/<version_job>/<spider>', None),
        ('overview/<opt>/<project>/<version_job>', dict(spider=None)),
        ('overview/<opt>/<project>', dict(version_job=None, spider=None)),
        ('overview/<opt>', dict(project=None, version_job=None, spider=None)),
        ('overview', dict(opt=None, project=None, version_job=None, spider=None))
    ])

    from .jobs.multinode import MultinodeView
    register_view(MultinodeView, 'multinode', [
        ('multinode/<opt>/<project>/<version_job>', None),
        ('multinode/<opt>/<project>', dict(version_job=None))
    ])

    # projects
    from .projects.deploy import DeployView, UploadView, DeployXhrView
    register_view(DeployView, 'deploy.deploy', [('deploy', None)])
    register_view(UploadView, 'deploy.upload', [('deploy/upload', None)])
    register_view(DeployXhrView, 'deploy.deploy_xhr', [('deploy/xhr/<eggname>/<project>/<version>', None)])

    from .projects.schedule import ScheduleView, CheckView, RunView, ScheduleXhrView
    register_view(ScheduleView, 'schedule.schedule', [
        ('schedule/<project>/<version>/<spider>', None),
        ('schedule/<project>/<version>', dict(spider=None)),
        ('schedule/<project>', dict(version=None, spider=None)),
        ('schedule', dict(project=None, version=None, spider=None))
    ])
    register_view(CheckView, 'schedule.check', [('schedule/check', None)])
    register_view(RunView, 'schedule.run', [('schedule/run', None)])
    register_view(ScheduleXhrView, 'schedule.schedule_xhr', [('schedule/xhr/<filename>', None)])

    from .projects.schedule import bp as bp_schedule_history
    app.register_blueprint(bp_schedule_history)

    from .projects.manage import ManageView
    register_view(ManageView, 'manage', [
        ('manage/<opt>/<project>/<version_spider_job>', None),
        ('manage/<opt>/<project>', dict(version_spider_job=None)),
        ('manage', dict(opt='listprojects', project=None, version_spider_job=None))
    ])

    # files
    from .files.log import LogView
    register_view(LogView, 'log', [('log/<opt>/<project>/<spider>/<job>', None)])

    from .files.logs import LogsView
    register_view(LogsView, 'logs', [
        ('logs/<project>/<spider>', None),
        ('logs/<project>', dict(spider=None)),
        ('logs', dict(project=None, spider=None))
    ])

    from .files.items import ItemsView
    register_view(ItemsView, 'items', [
        ('items/<project>/<spider>', None),
        ('items/<project>', dict(spider=None)),
        ('items', dict(project=None, spider=None))
    ])

    from .files.parse import UploadLogView, UploadedLogView
    register_view(UploadLogView, 'parse.upload', [('parse/upload', None)])
    register_view(UploadedLogView, 'parse.uploaded', [('parse/uploaded/<filename>', None)])

    from .files.parse import bp as bp_parse_source
    app.register_blueprint(bp_parse_source)

    # system
    from .system.settings import SettingsView
    register_view(SettingsView, 'settings', [('settings', None)])
