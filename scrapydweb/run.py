# coding: utf8
import argparse
import os
from shutil import copyfile
import sys

from flask import request

# from . import create_app  # --debug: ImportError: cannot import name 'create_app'
from scrapydweb import create_app
from scrapydweb.__version__ import __description__, __version__
from scrapydweb.utils.check_app_config import check_app_config
from scrapydweb.utils.utils import authenticate, find_scrapydweb_settings_py, printf
from scrapydweb.vars import LAST_CHECK_UPDATE_PATH


ALERT = '!' * 100
STAR = '*' * 100
CWD = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SETTINGS_PY_PATH = os.path.join(CWD, 'default_settings.py')
SCRAPYDWEB_SETTINGS_PY = 'scrapydweb_settings_v7.py'


def main():
    main_pid = os.getpid()
    printf("ScrapydWeb version: %s" % __version__)
    printf("Use 'scrapydweb -h' to get help")
    printf("Main pid: %s" % main_pid)
    printf("Loading default settings from %s" % DEFAULT_SETTINGS_PY_PATH)
    app = create_app()
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
        sys.exit("\n{alert}\n{err}\nCheck and update your settings in {path}\n{alert}".format(
                 alert=ALERT, err=err, path=app.config['SCRAPYDWEB_SETTINGS_PY_PATH']))

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
        return dict(
            SCRAPYD_SERVERS=app.config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800'],
            SCRAPYD_SERVERS_AMOUNT=len(app.config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800']),
            SCRAPYD_SERVERS_GROUPS=app.config.get('SCRAPYD_SERVERS_GROUPS', []) or [''],
            SCRAPYD_SERVERS_AUTHS=app.config.get('SCRAPYD_SERVERS_AUTHS', []) or [None],

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
        # printf("The environment variable 'FLASK_ENV' has been set to 'development'", warn=True)
        # printf("WARNING: Do not use the development server in a production. "
               # "Check out http://flask.pocoo.org/docs/1.0/deploying/", warn=True)

    # http://flask.pocoo.org/docs/1.0/config/?highlight=flask_debug#environment-and-debug-features
    if app.config.get('DEBUG', False):
        os.environ['FLASK_DEBUG'] = '1'
        printf("It's not recommended to run ScrapydWeb in debug mode, set 'DEBUG = False' instead.", warn=True)
    else:
        os.environ['FLASK_DEBUG'] = '0'

    # site-packages/flask/app.py
    # Threaded mode is enabled by default.
    # https://stackoverflow.com/a/28590266/10517783 to run in HTTP or HTTPS mode
    # site-packages/werkzeug/serving.py
    if app.config.get('ENABLE_HTTPS', False):
        protocol = 'https'
        context = (app.config['CERTIFICATE_FILEPATH'], app.config['PRIVATEKEY_FILEPATH'])
    else:
        protocol = 'http'
        context = None
    print(STAR)
    printf("Visit ScrapydWeb at {protocol}://127.0.0.1:{port} or {protocol}://IP-OF-THE-CURRENT-HOST:{port}".format(
           protocol=protocol, port=app.config['SCRAPYDWEB_PORT']))
    printf("For running Flask in production, check out http://flask.pocoo.org/docs/1.0/deploying/", warn=True)
    print(STAR)
    app.run(host=app.config['SCRAPYDWEB_BIND'], port=app.config['SCRAPYDWEB_PORT'], ssl_context=context)


def load_custom_settings(config):
    path = find_scrapydweb_settings_py(SCRAPYDWEB_SETTINGS_PY, os.getcwd())

    if path:
        config['SCRAPYDWEB_SETTINGS_PY_PATH'] = path
        print(STAR)
        printf("Overriding custom settings from %s" % path, warn=True)
        print(STAR)
        config.from_pyfile(path)
    else:
        try:
            os.remove(LAST_CHECK_UPDATE_PATH)
        except:
            pass

        try:
            copyfile(config['DEFAULT_SETTINGS_PY_PATH'], config['SCRAPYDWEB_SETTINGS_PY_PATH'])
        except:
            sys.exit("\n{alert}\nPlease copy the 'default_settings.py' file from the path above "
                     "to current working directory,\nand rename it to '{file}'.\n"
                     "Then add your SCRAPYD_SERVERS in the config file and restart scrapydweb.\n{alert}".format(
                      alert=ALERT, file=SCRAPYDWEB_SETTINGS_PY))
        else:
            sys.exit("\n{alert}\nThe config file '{file}' has been copied to current working directory.\n"
                     "Please add your SCRAPYD_SERVERS in the config file and restart scrapydweb.\n{alert}".format(
                      alert=ALERT, file=SCRAPYDWEB_SETTINGS_PY))


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

    ENABLE_LOGPARSER = config.get('ENABLE_LOGPARSER', True)
    parser.add_argument(
        '-dlp', '--disable_logparser',
        action='store_true',
        help=("current: ENABLE_LOGPARSER = %s, append '--disable_logparser' to disable running LogParser "
              "as a subprocess at startup") % ENABLE_LOGPARSER
    )

    ENABLE_EMAIL = config.get('ENABLE_EMAIL', False)
    parser.add_argument(
        '-de', '--disable_email',
        action='store_true',
        help="current: ENABLE_EMAIL = %s, append '--disable_email' to disable email notice" % ENABLE_EMAIL
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
    printf("Reading settings from command line: %s" % args)

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
    if args.disable_email:
        config['ENABLE_EMAIL'] = False
    if args.debug:
        config['DEBUG'] = True
    if args.verbose:
        config['VERBOSE'] = True


if __name__ == '__main__':
    main()
