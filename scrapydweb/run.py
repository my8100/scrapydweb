# coding: utf-8
import argparse
import logging
import os
from shutil import copyfile
import sys

from flask import request

# from . import create_app  # --debug: ImportError: cannot import name 'create_app'
from scrapydweb import create_app
from scrapydweb.__version__ import __description__, __version__
from scrapydweb.common import authenticate, find_scrapydweb_settings_py, handle_metadata, handle_slash
from scrapydweb.vars import ROOT_DIR, SCRAPYDWEB_SETTINGS_PY, SCHEDULER_STATE_DICT, STATE_PAUSED, STATE_RUNNING
from scrapydweb.utils.check_app_config import check_app_config


logger = logging.getLogger(__name__)
apscheduler_logger = logging.getLogger('apscheduler')

STAR = '\n%s\n' % ('*' * 100)
DEFAULT_SETTINGS_PY_PATH = os.path.join(ROOT_DIR, 'default_settings.py')


def main():
    apscheduler_logger.setLevel(logging.ERROR)  # To hide warning logging in scheduler.py until app.run()
    main_pid = os.getpid()
    logger.info("ScrapydWeb version: %s", __version__)
    logger.info("Use 'scrapydweb -h' to get help")
    logger.info("Main pid: %s", main_pid)
    logger.debug("Loading default settings from %s", handle_slash(DEFAULT_SETTINGS_PY_PATH))
    app = create_app()
    handle_metadata('main_pid', main_pid)  # In handle_metadata(): with db.app.app_context():
    app.config['MAIN_PID'] = main_pid
    app.config['DEFAULT_SETTINGS_PY_PATH'] = DEFAULT_SETTINGS_PY_PATH
    app.config['SCRAPYDWEB_SETTINGS_PY_PATH'] = os.path.join(os.getcwd(), SCRAPYDWEB_SETTINGS_PY)
    load_custom_settings(app.config)

    args = parse_args(app.config)
    # "scrapydweb -h" ends up here
    update_app_config(app.config, args)
    try:
        check_app_config(app.config)
    except AssertionError as err:
        logger.error("Check app config fail: ")
        sys.exit(u"\n{err}\n\nCheck and update your settings in {path}\n".format(
                 err=err, path=handle_slash(app.config['SCRAPYDWEB_SETTINGS_PY_PATH'])))

    # https://stackoverflow.com/questions/34164464/flask-decorate-every-route-at-once
    @app.before_request
    def require_login():
        if app.config.get('ENABLE_AUTH', False):
            auth = request.authorization
            USERNAME = str(app.config.get('USERNAME', ''))  # May be 0 from config file
            PASSWORD = str(app.config.get('PASSWORD', ''))
            if not auth or not (auth.username == USERNAME and auth.password == PASSWORD):
                return authenticate()

    # MUST be commented out for released version
    # https://stackoverflow.com/questions/34066804/disabling-caching-in-flask
    # @app.after_request
    # def add_header(r):
        # r.headers['Pragma'] = 'no-cache'
        # r.headers['Expires'] = '0'
        # r.headers['Cache-Control'] = 'public, max-age=0'
        # return r

    @app.context_processor
    def inject_variable():
        SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800']
        SCRAPYD_SERVERS_PUBLIC_URLS = app.config.get('SCRAPYD_SERVERS_PUBLIC_URLS', None)
        return dict(
            SCRAPYD_SERVERS=SCRAPYD_SERVERS,
            SCRAPYD_SERVERS_AMOUNT=len(SCRAPYD_SERVERS),
            SCRAPYD_SERVERS_GROUPS=app.config.get('SCRAPYD_SERVERS_GROUPS', []) or [''],
            SCRAPYD_SERVERS_AUTHS=app.config.get('SCRAPYD_SERVERS_AUTHS', []) or [None],
            SCRAPYD_SERVERS_PUBLIC_URLS=SCRAPYD_SERVERS_PUBLIC_URLS or [''] * len(SCRAPYD_SERVERS),

            DAEMONSTATUS_REFRESH_INTERVAL=app.config.get('DAEMONSTATUS_REFRESH_INTERVAL', 10),
            ENABLE_AUTH=app.config.get('ENABLE_AUTH', False),
            SHOW_SCRAPYD_ITEMS=app.config.get('SHOW_SCRAPYD_ITEMS', True),
        )

    # To solve https://github.com/my8100/scrapydweb/issues/17
    # http://flask.pocoo.org/docs/1.0/cli/?highlight=flask_debug#environments
    # flask/helpers.py: get_env() The default is 'production'
    # On Windows, get/set/delete: set FLASK_ENV, set FLASK_ENV=production, set set FLASK_ENV=
    # if not os.environ.get('FLASK_ENV'):
        # os.environ['FLASK_ENV'] = 'development'
        # print("The environment variable 'FLASK_ENV' has been set to 'development'")
        # print("WARNING: Do not use the development server in a production. "
               # "Check out http://flask.pocoo.org/docs/1.0/deploying/")

    # http://flask.pocoo.org/docs/1.0/config/?highlight=flask_debug#environment-and-debug-features
    if app.config.get('DEBUG', False):
        os.environ['FLASK_DEBUG'] = '1'
        logger.info("Note that use_reloader is set to False in run.py")
    else:
        os.environ['FLASK_DEBUG'] = '0'

    # site-packages/flask/app.py
    # Threaded mode is enabled by default.
    # https://stackoverflow.com/a/28590266/10517783 to run in HTTP or HTTPS mode
    # site-packages/werkzeug/serving.py
    # https://stackoverflow.com/questions/13895176/sqlalchemy-and-sqlite-database-is-locked
    if app.config.get('ENABLE_HTTPS', False):
        protocol = 'https'
        context = (app.config['CERTIFICATE_FILEPATH'], app.config['PRIVATEKEY_FILEPATH'])
    else:
        protocol = 'http'
        context = None

    print("{star}Visit ScrapydWeb at {protocol}://127.0.0.1:{port} "
          "or {protocol}://IP-OF-THE-CURRENT-HOST:{port}{star}\n".format(
           star=STAR, protocol=protocol, port=app.config['SCRAPYDWEB_PORT']))
    logger.info("For running Flask in production, check out http://flask.pocoo.org/docs/1.0/deploying/")
    apscheduler_logger.setLevel(logging.DEBUG)
    app.run(host=app.config['SCRAPYDWEB_BIND'], port=app.config['SCRAPYDWEB_PORT'],
            ssl_context=context, use_reloader=False)


def load_custom_settings(config):
    path = find_scrapydweb_settings_py(SCRAPYDWEB_SETTINGS_PY, os.getcwd())

    if path:
        config['SCRAPYDWEB_SETTINGS_PY_PATH'] = path
        print(u"{star}Overriding custom settings from {path}{star}".format(star=STAR, path=handle_slash(path)))
        config.from_pyfile(path)
    else:
        logger.error("%s not found: ", SCRAPYDWEB_SETTINGS_PY)
        try:
            copyfile(config['DEFAULT_SETTINGS_PY_PATH'], config['SCRAPYDWEB_SETTINGS_PY_PATH'])
        except:
            sys.exit("\nPlease copy the 'default_settings.py' file from the path above to current working directory,\n"
                     "and rename it to '{file}'.\n"
                     "Then add your SCRAPYD_SERVERS in the config file and restart scrapydweb.\n".format(
                      file=SCRAPYDWEB_SETTINGS_PY))
        else:
            sys.exit("\nATTENTION:\nYou may encounter ERROR if there are any running timer tasks added in v1.2.0,\n"
                     "and you have to restart scrapydweb and manually edit the tasks to resume them.\n"
                     "\nThe config file '{file}' has been copied to current working directory.\n"
                     "Please add your SCRAPYD_SERVERS in the config file and restart scrapydweb.\n".format(
                      file=SCRAPYDWEB_SETTINGS_PY))


def parse_args(config):
    parser = argparse.ArgumentParser(description='ScrapydWeb -- %s' % __description__)

    SCRAPYDWEB_BIND = config.get('SCRAPYDWEB_BIND', '0.0.0.0')
    parser.add_argument(
        '-b', '--bind',
        default=SCRAPYDWEB_BIND,
        help=("current: %s, note that setting to 0.0.0.0 or IP-OF-THE-CURRENT-HOST would make ScrapydWeb server "
              "visible externally, otherwise, type '-b 127.0.0.1'") % SCRAPYDWEB_BIND
    )

    SCRAPYDWEB_PORT = config.get('SCRAPYDWEB_PORT', 5000)
    parser.add_argument(
        '-p', '--port',
        default=SCRAPYDWEB_PORT,
        help="current: %s, accept connections on the specified port" % SCRAPYDWEB_PORT
    )

    SCRAPYD_SERVERS = config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800']
    parser.add_argument(
        '-ss', '--scrapyd_server',
        action='append',
        help=("current: %s, type '-ss 127.0.0.1 -ss username:password@192.168.123.123:6801#group' "
              "to set up more than one Scrapyd server to manage. ") % SCRAPYD_SERVERS
    )

    ENABLE_AUTH = config.get('ENABLE_AUTH', False)
    parser.add_argument(
        '-da', '--disable_auth',
        action='store_true',
        help="current: ENABLE_AUTH = %s, append '--disable_auth' to disable basic auth for web UI" % ENABLE_AUTH
    )

    ENABLE_LOGPARSER = config.get('ENABLE_LOGPARSER', False)
    parser.add_argument(
        '-dlp', '--disable_logparser',
        action='store_true',
        help=("current: ENABLE_LOGPARSER = %s, append '--disable_logparser' to disable running LogParser "
              "as a subprocess at startup") % ENABLE_LOGPARSER
    )

    SCHEDULER_STATE = SCHEDULER_STATE_DICT[handle_metadata().get('scheduler_state', STATE_RUNNING)]
    parser.add_argument(
        '-sw', '--switch_scheduler_state',
        action='store_true',
        help=("current: %s, append '--switch_scheduler_state' to switch the state of scheduler "
              "for timer tasks") % SCHEDULER_STATE
    )

    ENABLE_MONITOR = config.get('ENABLE_MONITOR', False)
    parser.add_argument(
        '-dm', '--disable_monitor',
        action='store_true',
        help="current: ENABLE_MONITOR = %s, append '--disable_monitor' to disable monitor" % ENABLE_MONITOR
    )

    DEBUG = config.get('DEBUG', False)
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help=("current: DEBUG = %s, append '--debug' to enable debug mode "
              "and the debugger would be available in the browser") % DEBUG
    )

    VERBOSE = config.get('VERBOSE', False)
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help=("current: VERBOSE = %s, append '--verbose' to set the logging level to DEBUG "
              "for getting more information about how ScrapydWeb works") % VERBOSE
    )

    return parser.parse_args()


def update_app_config(config, args):
    logger.debug("Reading settings from command line: %s", args)

    config.update(dict(
        SCRAPYDWEB_BIND=args.bind,
        SCRAPYDWEB_PORT=args.port,
    ))

    # scrapyd_server would be None if the -ss argument is not passed in
    if args.scrapyd_server:
        config['SCRAPYD_SERVERS'] = args.scrapyd_server

    # action='store_true': default False
    if args.disable_auth:
        config['ENABLE_AUTH'] = False
    if args.disable_logparser:
        config['ENABLE_LOGPARSER'] = False
    if args.switch_scheduler_state:
        if handle_metadata().get('scheduler_state', STATE_RUNNING) == STATE_RUNNING:
            handle_metadata('scheduler_state', STATE_PAUSED)
        else:
            handle_metadata('scheduler_state', STATE_RUNNING)
    if args.disable_monitor:
        config['ENABLE_MONITOR'] = False
    if args.debug:
        config['DEBUG'] = True
    if args.verbose:
        config['VERBOSE'] = True


if __name__ == '__main__':
    main()
