# coding: utf8
import os
import sys
import platform
from subprocess import Popen
import argparse
import re
import json
from shutil import copyfile, rmtree

from flask import request

from .vars import CACHE_PATH, DEFAULT_LATEST_VERSION, pattern_scrapyd_server
from .utils import json_dumps, authenticate, kill_child, on_parent_exit
from scrapydweb import create_app
from scrapydweb.__version__ import __version__, __description__, __url__


SCRAPYDWEB_SETTINGS_PY = 'scrapydweb_settings_v3.py'
CWD = os.path.dirname(os.path.abspath(__file__))
main_pid = os.getpid()


def main():
    print(">>> scrapydweb version: %s" % __version__)
    print(">>> Run 'scrapydweb -h' to get help")
    print(">>> Loading default settings from %s" % os.path.join(CWD, 'default_settings.py'))
    app = create_app()
    scrapydweb_settings_py = find_scrapydweb_settings_py()
    if scrapydweb_settings_py:
        print(">>> Overriding custom settings from %s" % scrapydweb_settings_py)
        app.config.from_pyfile(scrapydweb_settings_py)
    else:
        scrapydweb_settings_py = os.path.join('.', SCRAPYDWEB_SETTINGS_PY)
        try:
            copyfile(os.path.join(CWD, 'default_settings.py'), scrapydweb_settings_py)
            print(">>> The config file '%s' is copied to current working directory, "
                  "and you may custom settings with it" % SCRAPYDWEB_SETTINGS_PY)
        except:
            print(">>> You may copy the file 'default_settings.py' from above path to your working directory, "
                  "and rename it to '%s' to custom settings" % SCRAPYDWEB_SETTINGS_PY)

    args = parse_args(app.config)
    check_args(args)
    update_app_config(app.config, args)
    # from pprint import pprint
    # pprint(app.config)

    print(">>> Main pid: %s" % main_pid)
    if not app.config['DISABLE_CACHE']:
        import atexit
        caching_subprocess = start_caching(app.config)
        print(">>> Caching utf8 and stats files in the background with pid: %s" % caching_subprocess.pid)
        atexit.register(kill_child, caching_subprocess)

    print(">>> Visit ScrapydWeb at http://{bind}:{port} or http://127.0.0.1:{port}".format(
        bind='IP-OF-THE-HOST-WHERE-SCRAPYDWEB-RUNS-ON', port=app.config['SCRAPYDWEB_PORT']))


    username = app.config.get('USERNAME', '')
    password = app.config.get('PASSWORD', '')

    @app.context_processor
    def inject_variable():
        return {
            'SCRAPYD_SERVERS': app.config['SCRAPYD_SERVERS'],
            'SCRAPYD_SERVERS_GROUPS': app.config['SCRAPYD_SERVERS_GROUPS'],
            'SCRAPYD_SERVERS_AUTHS': app.config['SCRAPYD_SERVERS_AUTHS'],
            'DEFAULT_LATEST_VERSION': DEFAULT_LATEST_VERSION,
            'SCRAPYDWEB_VERSION': __version__,
            'GITHUB_URL': __url__,
            'REQUIRE_LOGIN': True if username and password else False,
            'SHOW_SCRAPYD_ITEMS': app.config.get('SHOW_SCRAPYD_ITEMS', True),
            'scrapydweb_settings_py': scrapydweb_settings_py,
            'DAEMONSTATUS_REFRESH_INTERVAL': int(app.config.get('DAEMONSTATUS_REFRESH_INTERVAL', 10)),
        }

    # https://stackoverflow.com/questions/34164464/flask-decorate-every-route-at-once
    @app.before_request
    def require_login():
        if request.form:
            app.logger.debug(json_dumps(request.form))
        if username and password:
            auth = request.authorization
            if not auth or not (auth.username == username and auth.password == password):
                return authenticate()

    # /site-packages/flask/app.py
        # def run(self, host=None, port=None, debug=None, load_dotenv=True, **options):
        # Threaded mode is enabled by default.
    app.run(host=app.config['SCRAPYDWEB_BIND'], port=app.config['SCRAPYDWEB_PORT'])  # , debug=True)


def find_scrapydweb_settings_py(path='.', prevpath=None):
    if path == prevpath:
        return ''
    path = os.path.abspath(path)
    cfgfile = os.path.join(path, SCRAPYDWEB_SETTINGS_PY)
    if os.path.exists(cfgfile):
        return cfgfile
    return find_scrapydweb_settings_py(os.path.dirname(path), path)


def parse_args(config):
    parser = argparse.ArgumentParser(description='ScrapydWeb -- %s' % __description__)


    default = config.get('SCRAPYDWEB_BIND', '0.0.0.0')
    parser.add_argument(
        '--bind',
        default=default,
        help=("default: %s, and 0.0.0.0 makes ScrapydWeb server visible externally, "
              "set to 127.0.0.1 to disable that") % default
    )

    default = config.get('SCRAPYDWEB_PORT', 5000)
    parser.add_argument(
        '-p', '--port',
        default=default,
        help="default: %s, the port where ScrapydWeb server run at" % default
    )

    default = str(config.get('USERNAME', '')) # May be 0 from config file
    parser.add_argument(
        '--username',
        default=default,
        help="default: %s, the username of basic auth for web UI" % default
    )

    default = str(config.get('PASSWORD', '')) # May be 0 from config file
    parser.add_argument(
        '--password',
        default=default,
        help="default: %s, the password of basic auth for web UI" % default
    )


    default = config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    parser.add_argument(
        '-ss', '--scrapyd_server',
        # default=default,
        action='append',
        help=("default: %s, type '-ss 127.0.0.1 -ss username:password@192.168.123.123:6801#group' "
              "to set any number of Scrapyd servers to control. "
              "See 'https://github.com/my8100/scrapydweb/blob/master/scrapydweb/default_settings.py' "
              "for more help") % (default or ['127.0.0.1:6800'])
    )


    default = config.get('SCRAPY_PROJECTS_DIR', '')
    parser.add_argument(
        '--scrapy_projects_dir',
        default=default,
        help=("default: %s, set to enable auto eggifying in Deploy page, "
              "e.g., C:/Users/username/myprojects/ or /home/username/myprojects/") % (default or "''")
    )

    default = config.get('SCRAPYD_LOGS_DIR', '')
    parser.add_argument(
        '--scrapyd_logs_dir',
        default=default,
        help=("default: %s, set to speed up loading utf8 and stats html, "
              "e.g., C:/Users/username/logs/ or /home/username/logs/ , "
              "The setting takes effect only when both ScrapydWeb and Scrapyd run on the same machine, "
              "and the Scrapyd server ip is added as '127.0.0.1'. "
              "See 'https://scrapyd.readthedocs.io/en/stable/config.html#logs-dir' "
              "to find out where the Scrapy logs are stored.") % (default or "''")
    )

    default = config.get('DISABLE_CACHE', False)
    parser.add_argument(
        '--disable_cache',
        action='store_true',
        help=("default: %s, append '--disable_cache' to disable caching utf8 and stats files "
              "in the background periodically") % default
    )

    default = config.get('DELETE_CACHE', False)
    parser.add_argument(
        '--delete_cache',
        action='store_true',
        help="default: %s, append '--delete_cache' to delete cached utf8 and stats files at startup" % default
    )

    default = config.get('DEBUG', False)
    parser.add_argument(
        '--debug',
        action='store_true',
        help=("default: %s, append '--debug' to enable debug mode "
              "and debugger would be available in the browser") % default
    )

    return parser.parse_args()


def check_args(args):
    print(">>> Reading settings from command line: %s" % args)

    username = args.username
    password = args.password
    if username or password:
        if not username:
            sys.exit("!!! In order to enable basic auth, the username should NOT be empty string: '%s'" % username)
        elif not password:
            sys.exit("!!! In order to enable basic auth, the password should NOT be empty string: '%s'" % password)
        else:
            print(">>> Enabling basic auth username/password: '%s'/'%s'" % (username, password))


    scrapy_projects_dir = args.scrapy_projects_dir
    if scrapy_projects_dir:
        if not os.path.isdir(scrapy_projects_dir):
            sys.exit("!!! scrapy_projects_dir NOT found: %s" % scrapy_projects_dir)
        else:
            print(">>> Using scrapy_projects_dir: %s" % scrapy_projects_dir)

    scrapyd_logs_dir = args.scrapyd_logs_dir
    if scrapyd_logs_dir:
        if not os.path.isdir(scrapyd_logs_dir):
            sys.exit("!!! scrapyd_logs_dir NOT found: %s" % scrapyd_logs_dir)
        else:
            print(">>> Using scrapyd_logs_dir: %s" % scrapyd_logs_dir)

    if args.delete_cache:
        if os.path.isdir(CACHE_PATH):
            rmtree(CACHE_PATH, ignore_errors=True)
            print(">>> Cache utf8 and stats files deleted")
        else:
            print("!!! Cache dir NOT found: %s" % CACHE_PATH)


def update_app_config(config, args):
    # scrapyd_server would be None if -ss not passed in
    if not args.scrapyd_server:
        args.scrapyd_server = config.get('SCRAPYD_SERVERS') or ['127.0.0.1:6800']

    config.update(dict(
        SCRAPYD_SERVERS=args.scrapyd_server,
        SCRAPYDWEB_BIND=args.bind,
        SCRAPYDWEB_PORT=args.port,
        USERNAME=args.username,
        PASSWORD=args.password,
        SCRAPY_PROJECTS_DIR=args.scrapy_projects_dir,
        SCRAPYD_LOGS_DIR=args.scrapyd_logs_dir,
    ))

    # action='store_true': default False
    if args.disable_cache:
        config['DISABLE_CACHE'] = True
    if args.delete_cache:
        config['DELETE_CACHE'] = True
    if args.debug:
        config['DEBUG'] = True

    SCRAPYD_SERVERS = config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    servers = []
    for idx, server in enumerate(SCRAPYD_SERVERS):
        if isinstance(server, tuple):
            assert len(server) == 5, "Scrapyd server should be a 5 elements tuple: %s" % str(server)
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


def start_caching(config):
    args = [
        sys.executable,
        os.path.join(CWD, 'cache.py'),

        str(main_pid),
        '127.0.0.1' if config['SCRAPYDWEB_BIND'] == '0.0.0.0' else config['SCRAPYDWEB_BIND'],
        str(config['SCRAPYDWEB_PORT']),
        config['USERNAME'],
        config['PASSWORD'],
        json.dumps(config['SCRAPYD_SERVERS']),
        json.dumps(config['SCRAPYD_SERVERS_AUTHS']),
        str(config['CACHE_ROUND_INTERVAL']),
        str(config['CACHE_REQUEST_INTERVAL']),
    ]

    # 'Windows':
        # AttributeError: module 'signal' has no attribute 'SIGKILL'
        # ValueError: preexec_fn is not supported on Windows platforms
    # macOS('Darwin'):
        # subprocess.SubprocessError: Exception occurred in preexec_fn.
        # OSError: dlopen(libc.so.6, 6): image not found
    if platform.system() == 'Linux':
        kwargs = dict(preexec_fn=on_parent_exit('SIGKILL')) # 'SIGTERM' 'SIGKILL'
        try:
            caching_subprocess = Popen(args, **kwargs)
        except Exception as err:
            print(err)
            caching_subprocess = Popen(args)
    else:
        caching_subprocess = Popen(args)

    return caching_subprocess


if __name__ == '__main__':
    main()
