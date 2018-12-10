# coding: utf8
import os
import sys
import argparse
from shutil import copyfile
from multiprocessing.dummy import Pool as ThreadPool

import requests
from flask import request

# from . import create_app  # --debug: ImportError: cannot import name 'create_app'
from scrapydweb import create_app
from scrapydweb.__version__ import __version__, __description__
from scrapydweb.vars import pattern_scrapyd_server, LAST_CHECK_UPDATE
from scrapydweb.utils.utils import printf, find_scrapydweb_settings_py, authenticate
from scrapydweb.utils.check_app_config import check_app_config
from scrapydweb.utils.init_caching import init_caching


CWD = os.path.dirname(os.path.abspath(__file__))
SCRAPYDWEB_SETTINGS_PY = 'scrapydweb_settings_v5.py'
scrapydweb_settings_py_path = os.path.join(os.getcwd(), SCRAPYDWEB_SETTINGS_PY)


def main():
    main_pid = os.getpid()
    printf("Main pid: %s" % main_pid)
    printf("ScrapydWeb version: %s" % __version__)
    printf("Use the 'scrapydweb -h' command to get help")
    printf("Loading default settings from %s" % os.path.join(CWD, 'default_settings.py'))

    app = create_app()
    load_custom_config(app.config)

    args = parse_args(app.config)
    # "scrapydweb -h" ends up here
    update_app_config(app.config, args)
    # from pprint import pprint
    # pprint(app.config)
    try:
        check_app_config(app.config)
    except AssertionError as err:
        sys.exit("\n!!! %s\nCheck and update your settings in: %s" % (err, scrapydweb_settings_py_path))

    if app.config.get('ENABLE_CACHE', True):
        caching_pid = init_caching(app.config, main_pid)
    else:
        caching_pid = None

    # https://stackoverflow.com/questions/34164464/flask-decorate-every-route-at-once
    @app.before_request
    def require_login():
        if app.config.get('ENABLE_AUTH', False):
            auth = request.authorization
            USERNAME = str(app.config.get('USERNAME', ''))  # May be 0 from config file
            PASSWORD = str(app.config.get('PASSWORD', ''))
            if not auth or not (auth.username == USERNAME and auth.password == PASSWORD):
                return authenticate()

    # Should be commented out for released version
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
            main_pid=main_pid,
            caching_pid=caching_pid,
            CHECK_LATEST_VERSION_FREQ=100,
            scrapydweb_settings_py_path=scrapydweb_settings_py_path,
        )

    printf("Visit ScrapydWeb at http://127.0.0.1:{port} or http://{bind}:{port}".format(
        bind='IP-OF-CURRENT-HOST', port=app.config['SCRAPYDWEB_PORT']))

    # site-packages/flask/app.py
    # def run(self, host=None, port=None, debug=None, load_dotenv=True, **options):
    # Threaded mode is enabled by default.
    app.run(host=app.config['SCRAPYDWEB_BIND'], port=app.config['SCRAPYDWEB_PORT'])  # , debug=True)


def load_custom_config(config):
    global scrapydweb_settings_py_path

    path = find_scrapydweb_settings_py(SCRAPYDWEB_SETTINGS_PY, os.getcwd())

    print('*' * 100)
    if path:
        scrapydweb_settings_py_path = path
        printf("Overriding custom settings from %s" % scrapydweb_settings_py_path, warn=True)
        config.from_pyfile(scrapydweb_settings_py_path)
    else:
        try:
            os.remove(LAST_CHECK_UPDATE)
        except:
            pass

        try:
            copyfile(os.path.join(CWD, 'default_settings.py'), scrapydweb_settings_py_path)
        except:
            sys.exit("Please copy the 'default_settings.py' file from above path to current working directory,\n"
                     "and rename it to '%s'.\n"
                     "Then add your SCRAPYD_SERVERS in the file and restart scrapydweb." % SCRAPYDWEB_SETTINGS_PY)
        else:
            sys.exit("The config file '%s' has been copied to current working directory.\n"
                     "Please add your SCRAPYD_SERVERS in the file and restart scrapydweb." % SCRAPYDWEB_SETTINGS_PY)


def parse_args(config):
    parser = argparse.ArgumentParser(description='ScrapydWeb -- %s' % __description__)

    SCRAPYDWEB_BIND = config.get('SCRAPYDWEB_BIND', '0.0.0.0')
    parser.add_argument(
        '-b', '--bind',
        default=SCRAPYDWEB_BIND,
        help=("current: %s, note that setting 0.0.0.0 or IP-OF-CURRENT-HOST makes ScrapydWeb server "
              "visible externally, otherwise, type '-b 127.0.0.1'") % SCRAPYDWEB_BIND
    )

    SCRAPYDWEB_PORT = config.get('SCRAPYDWEB_PORT', 5000)
    parser.add_argument(
        '-p', '--port',
        default=SCRAPYDWEB_PORT,
        help="current: %s, the port which ScrapydWeb would run on" % SCRAPYDWEB_PORT
    )

    SCRAPYD_SERVERS = config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800']
    parser.add_argument(
        '-ss', '--scrapyd_server',
        action='append',
        help=("current: %s, type '-ss 127.0.0.1 -ss username:password@192.168.123.123:6801#group' "
              "to set up more than one Scrapyd server to control. ") % SCRAPYD_SERVERS
    )

    ENABLE_AUTH = config.get('ENABLE_AUTH', False)
    parser.add_argument(
        '-da', '--disable_auth',
        action='store_true',
        help="current: ENABLE_AUTH = %s, append '--disable_auth' to disable basic auth for web UI" % ENABLE_AUTH
    )

    ENABLE_CACHE = config.get('ENABLE_CACHE', True)
    parser.add_argument(
        '-dc', '--disable_cache',
        action='store_true',
        help=("current: ENABLE_CACHE = %s, append '--disable_cache' to disable caching HTML for Log and Stats page "
              "in the background periodically") % ENABLE_CACHE
    )

    DELETE_CACHE = config.get('DELETE_CACHE', False)
    parser.add_argument(
        '-del', '--delete_cache',
        action='store_true',
        help=("current: DELETE_CACHE = %s, append '--delete_cache' to delete cached HTML files "
              "of Log and Stats page at startup" % DELETE_CACHE)
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
        help=("current: VERBOSE = %s, append '--verbose' to set logging level to DEBUG "
              "for getting more information about how ScrapydWeb works") % VERBOSE
    )

    return parser.parse_args()


def update_app_config(config, args):
    printf("Reading settings from command line: %s" % args)

    config.update(dict(
        SCRAPYDWEB_BIND=args.bind,
        SCRAPYDWEB_PORT=args.port,
    ))

    # scrapyd_server would be None if -ss not passed in
    SCRAPYD_SERVERS = args.scrapyd_server or config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800']
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
    check_scrapyd_connectivity(servers)

    config['SCRAPYD_SERVERS'] = ['%s:%s' % (ip, port) for group, ip, port, auth in servers]
    config['SCRAPYD_SERVERS_GROUPS'] = [group for group, ip, port, auth in servers]
    config['SCRAPYD_SERVERS_AUTHS'] = [auth for group, ip, port, auth in servers]

    # action='store_true': default False
    if args.disable_auth:
        config['ENABLE_AUTH'] = False
    if args.disable_cache:
        config['ENABLE_CACHE'] = False
    if args.delete_cache:
        config['DELETE_CACHE'] = True
    if args.disable_email:
        config['ENABLE_EMAIL'] = False
    if args.debug:
        config['DEBUG'] = True
    if args.verbose:
        config['VERBOSE'] = True


def check_scrapyd_connectivity(servers):
    printf("Checking connectivity of SCRAPYD_SERVERS")

    def check_connectivity(server):
        (group, ip, port, auth) = server
        try:
            r = requests.get('http://%s:%s' % (ip, port), auth=auth, timeout=3)
            assert r.status_code == 200
        except:
            return False
        else:
            return True

    # with ThreadPool(min(len(servers), 10)) as pool:  # Works in python 3.3 and up
        # results = pool.map(check_connectivity, servers)
    pool = ThreadPool(min(len(servers), 10))
    results = pool.map(check_connectivity, servers)
    pool.close()
    pool.join()

    print("Index {group:<20} {server:<21} Connectivity Auth".format(
          group='Group', server='Scrapyd IP:Port'))
    print('#' * 100)
    for idx, ((group, ip, port, auth), result) in enumerate(zip(servers, results), 1):
        print("{idx:_<5} {group:_<20} {server:_<22} {result:_<11} {auth}".format(
              idx=idx, group=group or 'None', server='%s:%s' % (ip, port), auth=auth, result=str(result)))
    print('#' * 100)

    if not any(results):
        sys.exit("\n!!! None of your SCRAPYD_SERVERS could be connected.\n"
                 "Check and update the SCRAPYD_SERVERS item in: %s" % scrapydweb_settings_py_path)


if __name__ == '__main__':
    main()
