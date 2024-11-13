# coding: utf-8
import logging
from logging.config import dictConfig
import platform
import re
import time
import traceback

from flask import Flask, current_app, render_template, url_for
from flask_compress import Compress
from logparser import __version__ as LOGPARSER_VERSION

from .__version__ import __url__, __version__
from .common import handle_metadata
from .models import Metadata, db
from .vars import PYTHON_VERSION, SQLALCHEMY_BINDS, SQLALCHEMY_DATABASE_URI
# from .utils.scheduler import scheduler


# https://stackoverflow.com/questions/18820274/how-to-suppress-sqlalchemy-engine-base-engine-logging-to-stdout
# logging.getLogger('sqlalchemy.engine.base.Engine').propagate = False
logging.getLogger('sqlalchemy.engine.base.Engine').setLevel(logging.WARNING)
# http://flask.pocoo.org/docs/1.0/logging/#basic-configuration
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)-8s in %(name)s: %(message)s',
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

# Comment out the dictConfig above first
# https://docs.sqlalchemy.org/en/latest/core/engines.html#configuring-logging
# https://apscheduler.readthedocs.io/en/latest/userguide.html#troubleshooting
# logging.basicConfig()
# logging.getLogger('apscheduler').setLevel(logging.DEBUG)
# logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)


def internal_server_error(error):
    kwargs = dict(
        error=error,
        traceback=traceback.format_exc(),
        url_issues=__url__ + '/issues',
        os=platform.platform(),
        python_version=PYTHON_VERSION,
        scrapydweb_version=__version__,
        logparser_version=LOGPARSER_VERSION,
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

    handle_db(app)
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


def handle_db(app):
    # https://flask-sqlalchemy.palletsprojects.com/en/master/config/
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_BINDS'] = SQLALCHEMY_BINDS
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # https://stackoverflow.com/a/33790196/10517783
    app.config['SQLALCHEMY_ECHO'] = True  # http://flask-sqlalchemy.pocoo.org/2.3/config/

    # flask_sqlalchemy/__init__.py
    # class SQLAlchemy(object):
    #     def __init__(self, app=None
    #         self.app = app
    #         if app is not None:
    #             self.init_app(app)
    db.app = app  # https://github.com/viniciuschiele/flask-apscheduler/blob/master/examples/flask_context.py
    db.init_app(app)  # http://flask-sqlalchemy.pocoo.org/2.3/contexts/
    db.create_all()

    # https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-vii-error-handling
    @app.teardown_request
    def handle_db_session(exception):
        if exception:
            db.session.rollback()
        db.session.remove()

    with db.app.app_context():
        if not Metadata.query.filter_by(version=__version__).first():
            metadata = Metadata(version=__version__)
            db.session.add(metadata)
            db.session.commit()
    if time.time() - handle_metadata().get('last_check_update_timestamp', time.time()) > 3600 * 24 * 30:
        handle_metadata('last_check_update_timestamp', time.time())
        handle_metadata('pageview', 0)
    else:
        handle_metadata('pageview', 1)
    # print(Metadata.query.filter_by(version=__version__).first())


def handle_route(app):
    def register_view(view, endpoint, url_defaults_list, with_node=True, trailing_slash=True):
        view_func = view.as_view(endpoint)
        for url, defaults in url_defaults_list:
            rule = '/<int:node>/%s' % url if with_node else '/%s' % url
            if trailing_slash:
                rule += '/'
            if not with_node:
                if defaults:
                    defaults['node'] = 1
                else:
                    defaults = dict(node=1)
            app.add_url_rule(rule, defaults=defaults, view_func=view_func)

    from .views.index import IndexView
    index_view = IndexView.as_view('index')
    app.add_url_rule('/<int:node>/', view_func=index_view)
    app.add_url_rule('/', defaults=dict(node=1), view_func=index_view)

    from .views.api import ApiView
    register_view(ApiView, 'api', [
        ('api/<opt>/<project>/<version_spider_job>', None),
        ('api/<opt>/<project>', dict(version_spider_job=None)),
        ('api/<opt>', dict(project=None, version_spider_job=None))
    ])

    from .views.baseview import MetadataView
    register_view(MetadataView, 'metadata', [('metadata', None)])

    # Overview
    from .views.overview.servers import ServersView
    register_view(ServersView, 'servers', [
        ('servers/getreports/<project>/<spider>/<version_job>', dict(opt='getreports')),
        ('servers/<opt>/<project>/<version_job>/<spider>', None),
        ('servers/<opt>/<project>/<version_job>', dict(spider=None)),
        ('servers/<opt>/<project>', dict(version_job=None, spider=None)),
        ('servers/<opt>', dict(project=None, version_job=None, spider=None)),
        ('servers', dict(opt=None, project=None, version_job=None, spider=None))
    ])

    from .views.overview.multinode import MultinodeView
    register_view(MultinodeView, 'multinode', [
        ('multinode/<opt>/<project>/<version_job>', None),
        ('multinode/<opt>/<project>', dict(version_job=None))
    ])

    from .views.overview.tasks import TasksView, TasksXhrView
    register_view(TasksView, 'tasks', [
        ('tasks/<int:task_id>/<int:task_result_id>', None),
        ('tasks/<int:task_id>', dict(task_result_id=None)),
        ('tasks', dict(task_id=None, task_result_id=None))
    ])
    register_view(TasksXhrView, 'tasks.xhr', [
        ('tasks/xhr/<action>/<int:task_id>/<int:task_result_id>', None),
        ('tasks/xhr/<action>/<int:task_id>', dict(task_result_id=None)),
        ('tasks/xhr/<action>', dict(task_id=None, task_result_id=None))
    ])

    from .views.overview.tasks import bp as bp_tasks_history
    app.register_blueprint(bp_tasks_history)

    # Dashboard
    from .views.dashboard.jobs import JobsView, JobsXhrView
    register_view(JobsView, 'jobs', [('jobs', None)])
    register_view(JobsXhrView, 'jobs.xhr', [('jobs/xhr/<action>/<int:id>', None)])

    from .views.dashboard.node_reports import NodeReportsView
    register_view(NodeReportsView, 'nodereports', [('nodereports', None)])

    from .views.dashboard.cluster_reports import ClusterReportsView
    register_view(ClusterReportsView, 'clusterreports', [
        ('clusterreports/<project>/<spider>/<job>', None),
        ('clusterreports', dict(project=None, spider=None, job=None))
    ])

    # Operations
    from .views.operations.deploy import DeployView, DeployUploadView, DeployXhrView
    register_view(DeployView, 'deploy', [('deploy', None)])
    register_view(DeployUploadView, 'deploy.upload', [('deploy/upload', None)])
    register_view(DeployXhrView, 'deploy.xhr', [('deploy/xhr/<eggname>/<project>/<version>', None)])

    from .views.operations.schedule import (ScheduleView, ScheduleCheckView, ScheduleRunView,
                                            ScheduleXhrView, ScheduleTaskView)
    register_view(ScheduleView, 'schedule', [
        ('schedule/<project>/<version>/<spider>', None),
        ('schedule/<project>/<version>', dict(spider=None)),
        ('schedule/<project>', dict(version=None, spider=None)),
        ('schedule', dict(project=None, version=None, spider=None))
    ])
    register_view(ScheduleCheckView, 'schedule.check', [('schedule/check', None)])
    register_view(ScheduleRunView, 'schedule.run', [('schedule/run', None)])
    register_view(ScheduleXhrView, 'schedule.xhr', [('schedule/xhr/<filename>', None)])
    register_view(ScheduleTaskView, 'schedule.task', [('schedule/task', None)])

    from .views.operations.schedule import bp as bp_schedule_history
    app.register_blueprint(bp_schedule_history)

    # Files
    from .views.files.log import LogView
    register_view(LogView, 'log', [('log/<opt>/<project>/<spider>/<job>', None)])

    from .views.files.logs import LogsView
    register_view(LogsView, 'logs', [
        ('logs/<project>/<spider>', None),
        ('logs/<project>', dict(spider=None)),
        ('logs', dict(project=None, spider=None))
    ])

    from .views.files.items import ItemsView
    register_view(ItemsView, 'items', [
        ('items/<project>/<spider>', None),
        ('items/<project>', dict(spider=None)),
        ('items', dict(project=None, spider=None))
    ])

    from .views.files.projects import ProjectsView
    register_view(ProjectsView, 'projects', [
        ('projects/<opt>/<project>/<version_spider_job>', None),
        ('projects/<opt>/<project>', dict(version_spider_job=None)),
        ('projects', dict(opt='listprojects', project=None, version_spider_job=None))
    ])

    # Parse Log
    from .views.utilities.parse import UploadLogView, UploadedLogView
    register_view(UploadLogView, 'parse.upload', [('parse/upload', None)])
    register_view(UploadedLogView, 'parse.uploaded', [('parse/uploaded/<filename>', None)])

    from .views.utilities.parse import bp as bp_parse_source
    app.register_blueprint(bp_parse_source)

    # Send text
    from .views.utilities.send_text import SendTextView, SendTextApiView
    register_view(SendTextView, 'sendtext', [('sendtext', None)])
    register_view(SendTextApiView, 'sendtextapi', [
        ('slack/<channel_chatid_subject>/<text>', dict(opt='slack')),
        ('slack/<text>', dict(opt='slack', channel_chatid_subject=None)),
        ('slack', dict(opt='slack', channel_chatid_subject=None, text=None)),
        ('telegram/<channel_chatid_subject>/<text>', dict(opt='telegram')),
        ('telegram/<text>', dict(opt='telegram', channel_chatid_subject=None)),
        ('telegram', dict(opt='telegram', channel_chatid_subject=None, text=None)),
        ('tg/<channel_chatid_subject>/<text>', dict(opt='tg')),
        ('tg/<text>', dict(opt='tg', channel_chatid_subject=None)),
        ('tg', dict(opt='tg', channel_chatid_subject=None, text=None)),
        ('email/<channel_chatid_subject>/<text>', dict(opt='email')),
        ('email/<text>', dict(opt='email', channel_chatid_subject=None)),
        ('email', dict(opt='email', channel_chatid_subject=None, text=None)),
    ], with_node=False, trailing_slash=False)

    # System
    from .views.system.settings import SettingsView
    register_view(SettingsView, 'settings', [('settings', None)])


def handle_template_context(app):
    STATIC = 'static'
    VERSION = 'v' + __version__.replace('.', '')
    # MUST be commented out for released version
    # VERSION = 'v131dev'

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
