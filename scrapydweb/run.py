# coding: utf8
import os
import sys
from shutil import copyfile
import re
import argparse
import subprocess
import shutil
import json

from flask import request, Response

from .vars import CACHE_PATH, DEFAULT_LATEST_VERSION
from scrapydweb import create_app
from scrapydweb.__version__ import __version__, __description__, __url__


CWD = os.path.dirname(os.path.abspath(__file__))


def main():
    print(">>> scrapydweb version: %s" % __version__)
    print(">>> Run 'scrapydweb -h' to get help")
    print(">>> Run ScrapydWeb with argument '-ss 127.0.0.1 -ss 192.168.0.101:12345@group1' "
          "to set any number of Scrapyd servers to control.")
    print(">>> Run ScrapydWeb with argument '--scrapyd_logs_dir SCRAPYD_LOGS_DIR' to speed up loading utf8 and stats html")
    print(">>> Run ScrapydWeb with argument '--disable_cache' to disable caching utf8 and stats files in the background periodically")

    print(">>> Using default settings from %s" % os.path.join(CWD, 'default_settings.py'))
    app = create_app()

    scrapydweb_settings_py = find_scrapydweb_settings_py()
    if scrapydweb_settings_py:
        print(">>> Overriding custom settings from %s" % scrapydweb_settings_py)
        app.config.from_pyfile(scrapydweb_settings_py)
    else:
        try:
            copyfile(os.path.join(CWD, 'default_settings.py'), os.path.join('.', 'scrapydweb_settings.py'))
            print(">>> The config file 'scrapydweb_settings.py' is copied to your working directory, "
                  "and you may custom settings with it")
        except:
            print(">>> You may copy the file 'default_settings.py' from above path to your working directory, "
                  "and rename it as 'scrapydweb_settings.py' to custom settings")

    args = parse_args(app.config)
    check_args(args)
    update_app_config(app.config, args)
    # print(app.config)

    if not app.config['DISABLE_CACHE']:
        start_caching(app.config)

    print('>>> Visit ScrapydWeb at http://{host}:{port} or http://127.0.0.1:{port}'.format(
        host="IP-OF-THE-HOST-WHERE-SCRAPYDWEB-RUNS-ON", port=app.config['SCRAPYDWEB_PORT']))


    username = str(app.config.get('USERNAME', ''))
    password = str(app.config.get('PASSWORD', ''))

    @app.context_processor
    def inject_variable():
        return {
            'SCRAPYD_SERVERS': app.config['SCRAPYD_SERVERS'],
            'SCRAPYD_SERVERS_GROUP': app.config['SCRAPYD_SERVERS_GROUP'],
            'DEFAULT_LATEST_VERSION': DEFAULT_LATEST_VERSION,
            'GITHUB_URL': __url__,
            'REQUIRE_LOGIN': True if username and password else False
        }

    # https://stackoverflow.com/questions/34164464/flask-decorate-every-route-at-once
    @app.before_request
    def require_login():
        if username and password:
            auth = request.authorization
            if not auth or not (auth.username == username and auth.password == password):
                return authenticate()

    # /site-packages/flask/app.py
    # run(host=None, port=None, debug=None, load_dotenv=True, **options)
    # Threaded mode is enabled by default.
    app.run(host=app.config['SCRAPYDWEB_HOST'], port=app.config['SCRAPYDWEB_PORT'])  # , debug=True)


def find_scrapydweb_settings_py(path='.', prevpath=None):
    if path == prevpath:
        return ''
    path = os.path.abspath(path)
    cfgfile = os.path.join(path, 'scrapydweb_settings.py')
    if os.path.exists(cfgfile):
        return cfgfile
    return find_scrapydweb_settings_py(os.path.dirname(path), path)


def parse_args(config):
    parser = argparse.ArgumentParser(description='ScrapydWeb -- %s' % __description__)

    default = config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    parser.add_argument(
        '-ss', '--scrapyd_server',
        # default=default,
        action='append',
        help=("default: %s, type '-ss 127.0.0.1 -ss 192.168.0.101:12345@group1' "
              "to set any number of Scrapyd servers to control. "
              "Default port would be 6800 if not provided, "
              "and group info is optional") % (default or ['127.0.0.1:6800'])
    )

    default = config.get('SCRAPYDWEB_HOST', '0.0.0.0')
    parser.add_argument(
        '-H', '--host',
        default=default,
        help=("default: %s, which makes ScrapydWeb server visible externally, "
              "set to 127.0.0.1 to disable that") % default
    )

    default = config.get('SCRAPYDWEB_PORT', 5000)
    parser.add_argument(
        '-p', '--port',
        default=default,
        help="default: %s, the port where ScrapydWeb server run at" % default
    )

    default = config.get('USERNAME', '')
    parser.add_argument(
        '--username',
        default=default,
        help="default: %s, the username of basic auth for web UI" % default
    )

    default = config.get('PASSWORD', '')
    parser.add_argument(
        '--password',
        default=default,
        help="default: %s, the password of basic auth for web UI" % default
    )

    default = config.get('SCRAPYD_LOGS_DIR', '')
    parser.add_argument(
        '--scrapyd_logs_dir',
        default=default,
        help=("default: %s , set to speed up loading utf8 and stats html, "
              "e.g. C:/Users/username/logs/ or /home/username/logs/ , "
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

    default = config.get('CACHE_INTERVAL_SECONDS', 300)
    parser.add_argument(
        '--cache_interval',
        type=float,
        default=default,
        help="default: %s, interval seconds while caching utf8 and stats files" % default
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
    print(">>> Settings from command line: %s" % args)

    username = args.username
    password = args.password
    if username or password:
        if not username:
            sys.exit("!!! username should NOT be empty string: %s" % username)
        elif not password:
            sys.exit("!!! password should NOT be empty string: %s" % password)
        else:
            print(">>> Using basic auth username/password: '%s'/'%s'" % (username, password))

    scrapyd_logs_dir = args.scrapyd_logs_dir
    if scrapyd_logs_dir:
        if not os.path.isdir(scrapyd_logs_dir):
            sys.exit("!!! scrapyd_logs_dir NOT found: %s" % scrapyd_logs_dir)
        else:
            print(">>> Using scrapyd_logs_dir: %s" % scrapyd_logs_dir)

    if args.delete_cache:
        if os.path.isdir(CACHE_PATH):
            shutil.rmtree(CACHE_PATH, ignore_errors=True)
            print('>>> Cache utf8 and stats files deleted')
        else:
            print('!!! Cache dir NOT found: %s' % CACHE_PATH)


def update_app_config(config, args):
    # scrapyd_server would be None if -ss not passed in
    if not args.scrapyd_server:
        args.scrapyd_server = config.get('SCRAPYD_SERVERS') or ['127.0.0.1:6800']

    config.update(dict(
        SCRAPYD_SERVERS=args.scrapyd_server,
        SCRAPYDWEB_HOST=args.host,
        SCRAPYDWEB_PORT=args.port,
        SCRAPYD_LOGS_DIR=args.scrapyd_logs_dir,
        CACHE_INTERVAl_SECONDS=args.cache_interval,
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
    for idx, s in enumerate(SCRAPYD_SERVERS):
        # if not re.search(r':\d{1,5}$', s):
        # SCRAPYD_SERVERS[idx] = s + ':6800'
        ip, port, group = re.search(r'^(.*?)(?:\:(.*?))?(?:@(.*?))?$', s.strip()).groups()
        ip = ip.strip() if ip and ip.strip() else '127.0.0.1'
        port = port.strip() if port and port.strip() else '6800'
        group = group.strip() if group and group.strip() else ''
        servers.append((group, ip, port))

    def key(arg):
        group, ip, port = arg
        parts = ip.split('.')
        parts = [('0' * (3 - len(part)) + part) for part in parts]
        return [group, '.'.join(parts), int(port)]

    servers = sorted(set(servers), key=key)

    # config['SCRAPYD_SERVERS'] = sorted(set(SCRAPYD_SERVERS))
    config['SCRAPYD_SERVERS'] = ['%s:%s' % (ip, port) for group, ip, port in servers]
    config['SCRAPYD_SERVERS_GROUP'] = [group for group, ip, port in servers]
    print(">>> SCRAPYD_SERVERS: %s" % config['SCRAPYD_SERVERS'])


# http://flask.pocoo.org/snippets/category/authentication/
def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response('<script>alert("FAIL to login. Basic auth is enabled since ScrapydWeb is running with argument '
                    '--username USERNAME and --password PASSWORD");</script>',
                    401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


def start_caching(config):
    args = [
        sys.executable,
        os.path.join(CWD, 'cache.py'),

        json.dumps(config['SCRAPYD_SERVERS']),
        '127.0.0.1' if config['SCRAPYDWEB_HOST'] == '0.0.0.0' else config['SCRAPYDWEB_HOST'],
        str(config['SCRAPYDWEB_PORT']),
        str(config['CACHE_INTERVAl_SECONDS']),
    ]
    subprocess.Popen(args)
    print('>>> Caching utf8 and stats files in the background')


if __name__ == '__main__':
    main()
