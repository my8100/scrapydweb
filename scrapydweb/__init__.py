# coding: utf8
import logging
from logging.config import dictConfig
import platform
import re
import sys
import traceback

from flask import Flask, current_app, render_template, url_for
from flask_compress import Compress

from .__version__ import __url__, __version__


PYTHON_VERSION = '.'.join([str(n) for n in sys.version_info[:3]])

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


def internal_server_error(error):
    kwargs = dict(
        error=error,
        traceback=traceback.format_exc(),
        url_issues=__url__ + '/issues',
        os=platform.platform(),
        python_version=PYTHON_VERSION,
        scrapydweb_version=__version__,
        scrapyd_servers_amount=len(current_app.config.get('SCRAPYD_SERVERS', []))
    )

    return render_template('500.html', **kwargs), 500


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
    handle_route(app)

    handle_template_context(app)

    # @app.errorhandler(404)
    # def handle_error(error):
        # return ('Nothing Found', 404)
    # http://flask.pocoo.org/docs/1.0/patterns/errorpages/
    app.register_error_handler(500, internal_server_error)

    # https://ansible-docs.readthedocs.io/zh/stable-2.0/rst/playbooks_filters.html#other-useful-filters
    # https://stackoverflow.com/questions/12791216/how-do-i-use-regular-expressions-in-jinja2
    # https://www.michaelcho.me/article/custom-jinja-template-filters-in-flask
    # http://flask.pocoo.org/docs/1.0/api/#flask.Flask.template_filter
    @app.template_filter()
    def regex_replace(s, find, replace):
        return re.sub(find, replace, s)
    app.jinja_env.variable_start_string = '{{ '
    app.jinja_env.variable_end_string = ' }}'

    compress = Compress()
    compress.init_app(app)

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


def handle_template_context(app):
    STATIC = 'static'
    VERSION = 'v' + __version__.replace('.', '')
    # MUST be commented out for released version
    # VERSION = 'v110'

    @app.context_processor
    def inject_variable():
        return dict(
            CHECK_LATEST_VERSION_FREQ=100,
            GITHUB_URL=__url__,
            PYTHON_VERSION=PYTHON_VERSION,
            SCRAPYDWEB_VERSION=__version__,

            # static_css_common=url_for(STATIC, filename='%s/css/common.css' % VERSION),
            static_css_dropdown=url_for(STATIC, filename='%s/css/dropdown.css' % VERSION),
            static_css_dropdown_mobileui=url_for(STATIC, filename='%s/css/dropdown_mobileui.css' % VERSION),
            static_css_icon_upload_icon_right=url_for(STATIC,
                                                      filename='%s/css/icon_upload_icon_right.css' % VERSION),
            static_css_multinode=url_for(STATIC, filename='%s/css/multinode.css' % VERSION),
            static_css_stacktable=url_for(STATIC, filename='%s/css/stacktable.css' % VERSION),
            static_css_stats=url_for(STATIC, filename='%s/css/stats.css' % VERSION),
            static_css_style=url_for(STATIC, filename='%s/css/style.css' % VERSION),
            static_css_style_mobileui=url_for(STATIC, filename='%s/css/style_mobileui.css' % VERSION),
            static_css_utf8=url_for(STATIC, filename='%s/css/utf8.css' % VERSION),
            static_css_utf8_mobileui=url_for(STATIC, filename='%s/css/utf8_mobileui.css' % VERSION),

            static_css_element_ui_index=url_for(STATIC,
                                                filename='%s/element-ui@2.4.6/lib/theme-chalk/index.css' % VERSION),
            static_js_element_ui_index=url_for(STATIC, filename='%s/element-ui@2.4.6/lib/index.js' % VERSION),

            static_js_common=url_for(STATIC, filename='%s/js/common.js' % VERSION),
            static_js_echarts_min=url_for(STATIC, filename='%s/js/echarts.min.js' % VERSION),
            static_js_icons_menu=url_for(STATIC, filename='%s/js/icons_menu.js' % VERSION),
            # static_js_github_buttons_html=url_for(STATIC, filename='%s/js/github_buttons.html' % VERSION),
            static_js_github_buttons=url_for(STATIC, filename='%s/js/github_buttons.js' % VERSION),
            static_js_jquery_min=url_for(STATIC, filename='%s/js/jquery.min.js' % VERSION),
            static_js_multinode=url_for(STATIC, filename='%s/js/multinode.js' % VERSION),
            static_js_stacktable=url_for(STATIC, filename='%s/js/stacktable.js' % VERSION),
            static_js_stats=url_for(STATIC, filename='%s/js/stats.js' % VERSION),
            static_js_vue_min=url_for(STATIC, filename='%s/js/vue.min.js' % VERSION),

            static_icon=url_for(STATIC, filename='%s/icon/fav.ico' % VERSION),
            static_icon_shortcut=url_for(STATIC, filename='%s/icon/fav.ico' % VERSION),
            static_icon_apple_touch=url_for(STATIC, filename='%s/icon/spiderman.png' % VERSION),
        )
