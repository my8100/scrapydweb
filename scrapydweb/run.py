# coding: utf8
import os
import sys
import argparse
from shutil import copyfile

from flask import request

# from . import create_app  # --debug: ImportError: cannot import name 'create_app'
from scrapydweb import create_app
from scrapydweb.__version__ import __version__, __description__, __url__
from scrapydweb.vars import DEFAULT_LATEST_VERSION, pattern_scrapyd_server
from scrapydweb.utils.utils import printf, json_dumps, find_scrapydweb_settings_py, authenticate
from scrapydweb.utils.check_app_config import check_app_config
from scrapydweb.utils.init_caching import init_caching


CWD = os.path.dirname(os.path.abspath(__file__))
SCRAPYDWEB_SETTINGS_PY = 'scrapydweb_settings_v4.py'
scrapydweb_settings_py_path = os.path.join(os.getcwd(), SCRAPYDWEB_SETTINGS_PY)


def main():
    main_pid = os.getpid()
    printf("Main pid: %s" % main_pid)
    printf("scrapydweb version: %s" % __version__)
    printf("Run 'scrapydweb -h' to get help")
    printf("Loading default settings from %s" % os.path.join(CWD, 'default_settings.py'))

    app = create_app()
    load_custom_config(app.config)

    args = parse_args(app.config)
    # "scrapydweb -h" would end up here
    update_app_config(app.config, args)
    # from pprint import pprint
    # pprint(app.config)
    try:
        check_app_config(app.config)
    except AssertionError as err:
        sys.exit("\n!!! %s\nCheck out your settings in: %s" % (err, scrapydweb_settings_py_path))

    if not app.config.get('DISABLE_CACHE', False):
        caching_pid = init_caching(app.config, main_pid)
    else:
        caching_pid = None

    REQUIRE_LOGIN = False if app.config.get('DISABLE_AUTH', True) else True
    USERNAME = str(app.config.get('USERNAME', ''))  # May be 0 from config file
    PASSWORD = str(app.config.get('PASSWORD', ''))

    # https://stackoverflow.com/questions/34164464/flask-decorate-every-route-at-once
    @app.before_request
    def require_login():
        if REQUIRE_LOGIN:
            auth = request.authorization
            if not auth or not (auth.username == USERNAME and auth.password == PASSWORD):
                return authenticate()

    @app.context_processor
    def inject_variable():
        return dict(
            SCRAPYD_SERVERS=app.config['SCRAPYD_SERVERS'],
            SCRAPYD_SERVERS_AMOUNT=len(app.config['SCRAPYD_SERVERS']),
            SCRAPYD_SERVERS_GROUPS=app.config['SCRAPYD_SERVERS_GROUPS'],
            SCRAPYD_SERVERS_AUTHS=app.config['SCRAPYD_SERVERS_AUTHS'],
            PYTHON_VERSION='.'.join([str(n) for n in sys.version_info[:3]]),
            SCRAPYDWEB_VERSION=__version__,
            CHECK_LATEST_VERSION_FREQ=30,
            DEFAULT_LATEST_VERSION=DEFAULT_LATEST_VERSION,
            GITHUB_URL=__url__,
            SHOW_SCRAPYD_ITEMS=app.config.get('SHOW_SCRAPYD_ITEMS', True),
            DAEMONSTATUS_REFRESH_INTERVAL=int(app.config.get('DAEMONSTATUS_REFRESH_INTERVAL', 10)),
            REQUIRE_LOGIN=REQUIRE_LOGIN,
            scrapydweb_settings_py_path=scrapydweb_settings_py_path,
            main_pid=main_pid,
            caching_pid=caching_pid,
        )

    printf("Visit ScrapydWeb at http://{bind}:{port} or http://127.0.0.1:{port}".format(
        bind='IP-OF-CURRENT-HOST', port=app.config['SCRAPYDWEB_PORT']))

    # /site-packages/flask/app.py
    # def run(self, host=None, port=None, debug=None, load_dotenv=True, **options):
    # Threaded mode is enabled by default.
    app.run(host=app.config['SCRAPYDWEB_BIND'], port=app.config['SCRAPYDWEB_PORT'])  # , debug=True)


def load_custom_config(config):
    global scrapydweb_settings_py_path

    path = find_scrapydweb_settings_py(SCRAPYDWEB_SETTINGS_PY, os.getcwd())

    print('')
    if path:
        scrapydweb_settings_py_path = path
        printf("Overriding custom settings from %s" % scrapydweb_settings_py_path, warn=True)
        config.from_pyfile(scrapydweb_settings_py_path)
    else:
        try:
            copyfile(os.path.join(CWD, 'default_settings.py'), scrapydweb_settings_py_path)
            printf("The config file '%s' is copied to current working directory, "
                   "and you can custom settings in it" % SCRAPYDWEB_SETTINGS_PY, warn=True)
        except:
            sys.exit("!!! Please copy the file 'default_settings.py' from above path to current working directory, "
                     "and rename it to '%s' to custom settings" % SCRAPYDWEB_SETTINGS_PY)
    print('')


def parse_args(config):
    parser = argparse.ArgumentParser(description='ScrapydWeb -- %s' % __description__)

    default = config.get('SCRAPYDWEB_BIND', '0.0.0.0')
    parser.add_argument(
        '--bind',
        default=default,
        help=("current: %s, note that setting 0.0.0.0 or IP-OF-CURRENT-HOST makes ScrapydWeb server "
              "visible externally, otherwise, set 127.0.0.1 to disable that") % default
    )

    default = config.get('SCRAPYDWEB_PORT', 5000)
    parser.add_argument(
        '-p', '--port',
        default=default,
        help="current: %s, the port which ScrapydWeb would run on" % default
    )

    default = config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    parser.add_argument(
        '-ss', '--scrapyd_server',
        # default=default,
        action='append',
        help=("current: %s, type '-ss 127.0.0.1 -ss username:password@192.168.123.123:6801#group' "
              "to set up any number of Scrapyd servers to control. ") % (default or ['127.0.0.1:6800'])
    )

    default = config.get('DISABLE_AUTH', True)
    parser.add_argument(
        '--disable_auth',
        action='store_true',
        help="current: %s, append '--disable_auth' to disable basic auth for web UI" % default
    )

    default = config.get('DISABLE_CACHE', False)
    parser.add_argument(
        '--disable_cache',
        action='store_true',
        help=("current: %s, append '--disable_cache' to disable caching HTML for Log and Stats page "
              "in the background periodically") % default
    )

    default = config.get('DELETE_CACHE', False)
    parser.add_argument(
        '--delete_cache',
        action='store_true',
        help="current: %s, append '--delete_cache' to delete cached HTML files of Log and Stats page at startup" % default
    )

    default = config.get('DISABLE_EMAIL', True)
    parser.add_argument(
        '--disable_email',
        action='store_true',
        help="current: %s, append '--disable_email' to disable email notice" % default
    )

    default = config.get('DEBUG', False)
    parser.add_argument(
        '--debug',
        action='store_true',
        help=("current: %s, append '--debug' to enable debug mode "
              "and the debugger would be available in the browser") % default
    )

    default = config.get('VERBOSE', False)
    parser.add_argument(
        '--verbose',
        action='store_true',
        help=("current: %s, append '--verbose' to set logging leverl to DEBUG "
              "for getting more information about how ScrapydWeb works") % default
    )

    return parser.parse_args()


def update_app_config(config, args):
    printf("Reading settings from command line: %s" % args)

    config.update(dict(
        SCRAPYDWEB_BIND=args.bind,
        SCRAPYDWEB_PORT=args.port,
    ))

    # scrapyd_server would be None if -ss not passed in
    SCRAPYD_SERVERS = args.scrapyd_server or config.get('SCRAPYD_SERVERS') or ['127.0.0.1:6800']
    servers = []
    for idx, server in enumerate(SCRAPYD_SERVERS):
        if isinstance(server, tuple):
            assert len(server) == 5, ("Scrapyd server should be a tuple with 5 elements, "
                                      "current value: %s" % str(server))
            usr, psw, ip, port, group = server
        else:
            usr, psw, ip, port, group = pattern_scrapyd_server.search(server.strip()).groups()
        ip = ip.strip() if ip and ip.strip() else '127.0.0.1'
        port = port.strip() if port and port.strip() else '6800'
        group = group.strip() if group and group.strip() else ''
        auth = (usr, psw) if usr and psw else None
        servers.append((group, ip, port, auth))

    def key(arg):
        group, ip, port, auth = arg
        parts = ip.split('.')
        parts = [('0' * (3 - len(part)) + part) for part in parts]
        return [group, '.'.join(parts), int(port)]

    servers = sorted(set(servers), key=key)

    print("{idx} {group:<10} {server:<21} {auth}".format(
          idx='Index', group='Group', server='Scrapyd IP:Port', auth='Auth'))
    print('#'*60)
    for idx, (group, ip, port, auth) in enumerate(servers, 1):
        print("{idx:_<5} {group:_<10} {server:_<21} {auth}".format(
              idx=idx, group=group or 'None', server='%s:%s' % (ip, port), auth=auth))
    print('#'*60)
    config['SCRAPYD_SERVERS'] = ['%s:%s' % (ip, port) for group, ip, port, auth in servers]
    config['SCRAPYD_SERVERS_GROUPS'] = [group for group, ip, port, auth in servers]
    config['SCRAPYD_SERVERS_AUTHS'] = [auth for group, ip, port, auth in servers]

    # action='store_true': default False
    if args.disable_auth:
        config['DISABLE_AUTH'] = True
    if args.disable_cache:
        config['DISABLE_CACHE'] = True
    if args.delete_cache:
        config['DELETE_CACHE'] = True
    if args.disable_email:
        config['DISABLE_EMAIL'] = True
    if args.debug:
        config['DEBUG'] = True
    if args.verbose:
        config['VERBOSE'] = True


if __name__ == '__main__':
    main()
