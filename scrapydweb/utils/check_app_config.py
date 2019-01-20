# coding: utf8
from multiprocessing.dummy import Pool as ThreadPool
import os
import re
import sys

import requests

from ..vars import ALLOWED_SCRAPYD_LOG_EXTENSIONS, EMAIL_TRIGGER_KEYS
from .send_email import send_email
from .sub_process import init_logparser, init_poll
from .utils import printf, json_dumps


EMAIL_PATTERN = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
HASH = '#' * 100
# r'^(?:(?:(.*?)\:)(?:(.*?)@))?(.*?)(?:\:(.*?))?(?:#(.*?))?$'
SCRAPYD_SERVER_PATTERN = re.compile(r"""
                                        ^
                                        (?:
                                            (?:(.*?):)      # username:
                                            (?:(.*?)@)      # password@
                                        )?
                                        (.*?)               # ip
                                        (?::(.*?))?         # :port
                                        (?:\#(.*?))?        # #group
                                        $
                                    """, re.X)


def check_app_config(config):
    def check_assert(key, default, is_instance, allow_zero=True, non_empty=False, containing_type=None):
        if is_instance is int:
            if allow_zero:
                should_be = "a non-negative integer"
            else:
                should_be = "a positive integer"
        else:
            should_be = "an instance of %s%s" % (is_instance, ' and NOT empty' if non_empty else '')

        value = config.get(key, default)
        kwargs = dict(
            key=key,
            should_be=should_be,
            containing_type=', containing elements of type %s' % containing_type if containing_type else '',
            value="'%s'" % value if isinstance(value, str) else value
        )
        to_assert = "{key} should be {should_be}{containing_type}. Current value: {value}".format(**kwargs)

        assert (isinstance(value, is_instance)
                and (not isinstance(value, bool) if is_instance is int else True)  # isinstance(True, int) => True
                and (value > (-1 if allow_zero else 0) if is_instance is int else True)
                and (value if non_empty else True)
                and (all([isinstance(i, containing_type) for i in value]) if containing_type else True)), to_assert
    printf("Checking app config:")

    # ScrapydWeb
    check_assert('SCRAPYDWEB_BIND', '0.0.0.0', str, non_empty=True)
    SCRAPYDWEB_PORT = config.get('SCRAPYDWEB_PORT', 5000)
    try:
        assert not isinstance(SCRAPYDWEB_PORT, bool)
        SCRAPYDWEB_PORT = int(SCRAPYDWEB_PORT)
        assert SCRAPYDWEB_PORT > 0
    except (TypeError, ValueError, AssertionError):
        sys.exit("SCRAPYDWEB_PORT should be a positive integer. Current value: %s" % SCRAPYDWEB_PORT)

    check_assert('ENABLE_AUTH', False, bool)
    if config.get('ENABLE_AUTH', False):
        # May be 0 from config file
        check_assert('USERNAME', '', str, non_empty=True)
        check_assert('PASSWORD', '', str, non_empty=True)
        printf("Basic auth enabled with USERNAME/PASSWORD: '%s'/'%s'" % (config['USERNAME'], config['PASSWORD']))

    check_assert('ENABLE_HTTPS', False, bool)
    if config.get('ENABLE_HTTPS', False):
        printf("HTTPS mode enabled: ENABLE_HTTPS = True")
        for k in ['CERTIFICATE_FILEPATH', 'PRIVATEKEY_FILEPATH']:
            check_assert(k, '', str, non_empty=True)
            assert os.path.isfile(config[k]), "%s NOT found: %s" % (k, config[k])
        printf("Running in HTTPS mode: %s, %s" % (config['CERTIFICATE_FILEPATH'], config['PRIVATEKEY_FILEPATH']))

    # Scrapy
    check_assert('SCRAPY_PROJECTS_DIR', '', str)
    SCRAPY_PROJECTS_DIR = config.get('SCRAPY_PROJECTS_DIR', '')
    if SCRAPY_PROJECTS_DIR:
        assert os.path.isdir(SCRAPY_PROJECTS_DIR), "SCRAPY_PROJECTS_DIR NOT found: %s" % SCRAPY_PROJECTS_DIR
        printf("Using SCRAPY_PROJECTS_DIR: %s" % SCRAPY_PROJECTS_DIR)

    # Scrapyd
    check_scrapyd_servers(config)

    check_assert('SCRAPYD_LOGS_DIR', '', str)
    SCRAPYD_LOGS_DIR = config.get('SCRAPYD_LOGS_DIR', '')
    if SCRAPYD_LOGS_DIR:
        assert os.path.isdir(SCRAPYD_LOGS_DIR), "SCRAPYD_LOGS_DIR NOT found: %s" % SCRAPYD_LOGS_DIR
        printf("Using SCRAPYD_LOGS_DIR: %s" % SCRAPYD_LOGS_DIR)
    else:
        _path = os.path.join(os.path.expanduser('~'), 'logs')
        if os.path.isdir(_path):
            config['SCRAPYD_LOGS_DIR'] = _path
            printf("Found SCRAPYD_LOGS_DIR: %s" % config['SCRAPYD_LOGS_DIR'])

    check_assert('SCRAPYD_LOG_EXTENSIONS', ALLOWED_SCRAPYD_LOG_EXTENSIONS, list, non_empty=True, containing_type=str)
    SCRAPYD_LOG_EXTENSIONS = config.get('SCRAPYD_LOG_EXTENSIONS', ALLOWED_SCRAPYD_LOG_EXTENSIONS)
    assert all([not i or i.startswith('.') for i in SCRAPYD_LOG_EXTENSIONS]), \
        ("SCRAPYD_LOG_EXTENSIONS should be a list like %s. "
         "Current value: %s" % (ALLOWED_SCRAPYD_LOG_EXTENSIONS, SCRAPYD_LOG_EXTENSIONS))
    printf("Locating scrapy log with SCRAPYD_LOG_EXTENSIONS: %s" % SCRAPYD_LOG_EXTENSIONS)

    # LogParser
    check_assert('ENABLE_LOGPARSER', True, bool)
    if config.get('ENABLE_LOGPARSER', True):
        assert config.get('SCRAPYD_LOGS_DIR', ''), \
            ("In order to automatically run LogParser at startup, you have to set up the 'SCRAPYD_LOGS_DIR' item "
             "first.\nOtherwise, set 'ENABLE_LOGPARSER = False' if you are not running any Scrapyd service "
             "on the current ScrapydWeb host.\nNote that you can run the LogParser service separately "
             "via command 'logparser' as you like.")

    # Page Display
    check_assert('SHOW_SCRAPYD_ITEMS', True, bool)
    check_assert('SHOW_DASHBOARD_JOB_COLUMN', False, bool)
    check_assert('DASHBOARD_FINISHED_JOBS_LIMIT', 0, int)
    check_assert('DASHBOARD_RELOAD_INTERVAL', 300, int)
    check_assert('DAEMONSTATUS_REFRESH_INTERVAL', 10, int)

    # Email Notice
    check_assert('ENABLE_EMAIL', False, bool)
    if config.get('ENABLE_EMAIL', False):
        check_assert('SMTP_SERVER', '', str, non_empty=True)
        check_assert('SMTP_PORT', 0, int, allow_zero=False)
        check_assert('SMTP_OVER_SSL', False, bool)
        check_assert('SMTP_CONNECTION_TIMEOUT', 10, int, allow_zero=False)

        check_assert('FROM_ADDR', '', str, non_empty=True)
        FROM_ADDR = config['FROM_ADDR']
        assert re.search(EMAIL_PATTERN, FROM_ADDR), \
            "FROM_ADDR should contain '@', like 'username@gmail.com'. Current value: %s" % FROM_ADDR
        check_assert('EMAIL_PASSWORD', '', str, non_empty=True)
        check_assert('TO_ADDRS', [], list, non_empty=True, containing_type=str)
        TO_ADDRS = config['TO_ADDRS']
        assert all([re.search(EMAIL_PATTERN, i) for i in TO_ADDRS]), \
            "All elements in TO_ADDRS should contain '@', like 'username@gmail.com'. Current value: %s" % TO_ADDRS

        # For compatibility with Python 3 using range()
        try:
            config['EMAIL_WORKING_DAYS'] = list(config.get('EMAIL_WORKING_DAYS', []))
        except TypeError:
            pass
        check_assert('EMAIL_WORKING_DAYS', [], list, non_empty=True, containing_type=int)
        EMAIL_WORKING_DAYS = config['EMAIL_WORKING_DAYS']
        assert all([not isinstance(i, bool) and i in range(1, 8) for i in EMAIL_WORKING_DAYS]), \
            "Element in EMAIL_WORKING_DAYS should be between 1 and 7. Current value: %s" % EMAIL_WORKING_DAYS

        try:
            config['EMAIL_WORKING_HOURS'] = list(config.get('EMAIL_WORKING_HOURS', []))
        except TypeError:
            pass
        check_assert('EMAIL_WORKING_HOURS', [], list, non_empty=True, containing_type=int)
        EMAIL_WORKING_HOURS = config['EMAIL_WORKING_HOURS']
        assert all([not isinstance(i, bool) and i in range(24) for i in EMAIL_WORKING_HOURS]), \
            "Element in EMAIL_WORKING_HOURS should be between 0 and 23. Current value: %s" % EMAIL_WORKING_HOURS

        check_assert('POLL_ROUND_INTERVAL', 300, int, allow_zero=False)
        check_assert('POLL_REQUEST_INTERVAL', 10, int, allow_zero=False)

        check_assert('ON_JOB_RUNNING_INTERVAL', 0, int)
        check_assert('ON_JOB_FINISHED', False, bool)

        for k in EMAIL_TRIGGER_KEYS:
            check_assert('LOG_%s_THRESHOLD' % k, 0, int)
            check_assert('LOG_%s_TRIGGER_STOP' % k, False, bool)
            check_assert('LOG_%s_TRIGGER_FORCESTOP' % k, False, bool)

        check_email(config)

    # System
    check_assert('DEBUG', False, bool)
    check_assert('VERBOSE', False, bool)

    # Subprocess
    init_subprocess(config)


def check_scrapyd_servers(config):
    SCRAPYD_SERVERS = config.get('SCRAPYD_SERVERS', []) or ['127.0.0.1:6800']
    servers = []
    for idx, server in enumerate(SCRAPYD_SERVERS):
        if isinstance(server, tuple):
            assert len(server) == 5, ("Scrapyd server should be a tuple of 5 elements, "
                                      "current value: %s" % str(server))
            usr, psw, ip, port, group = server
        else:
            usr, psw, ip, port, group = re.search(SCRAPYD_SERVER_PATTERN, server.strip()).groups()
        ip = ip.strip() if ip and ip.strip() else '127.0.0.1'
        port = port.strip() if port and port.strip() else '6800'
        group = group.strip() if group and group.strip() else ''
        auth = (usr, psw) if usr and psw else None
        servers.append((group, ip, port, auth))

    def key_func(arg):
        group, ip, port, auth = arg
        parts = ip.split('.')
        parts = [('0' * (3 - len(part)) + part) for part in parts]
        return [group, '.'.join(parts), int(port)]

    servers = sorted(set(servers), key=key_func)
    check_scrapyd_connectivity(servers, config['SCRAPYDWEB_SETTINGS_PY_PATH'])

    config['SCRAPYD_SERVERS'] = ['%s:%s' % (ip, port) for group, ip, port, auth in servers]
    config['SCRAPYD_SERVERS_GROUPS'] = [group for group, ip, port, auth in servers]
    config['SCRAPYD_SERVERS_AUTHS'] = [auth for group, ip, port, auth in servers]


def check_scrapyd_connectivity(servers, scrapydweb_settings_py_path=''):
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

    # with ThreadPool(min(len(servers), 100)) as pool:  # Works in python 3.3 and up
        # results = pool.map(check_connectivity, servers)
    pool = ThreadPool(min(len(servers), 100))
    results = pool.map(check_connectivity, servers)
    pool.close()
    pool.join()

    print("\nIndex {group:<20} {server:<21} Connectivity Auth".format(
          group='Group', server='Scrapyd IP:Port'))
    print(HASH)
    for idx, ((group, ip, port, auth), result) in enumerate(zip(servers, results), 1):
        print("{idx:_<5} {group:_<20} {server:_<22} {result:_<11} {auth}".format(
              idx=idx, group=group or 'None', server='%s:%s' % (ip, port), auth=auth, result=str(result)))
    print(HASH + '\n')

    if not any(results):
        sys.exit("\n!!! None of your SCRAPYD_SERVERS could be connected.\n"
                 "Check and update the SCRAPYD_SERVERS item in %s" % scrapydweb_settings_py_path)


def check_email(config):
    kwargs = dict(
        smtp_server=config['SMTP_SERVER'],
        smtp_port=config['SMTP_PORT'],
        smtp_over_ssl=config.get('SMTP_OVER_SSL', False),
        smtp_connection_timeout=config.get('SMTP_CONNECTION_TIMEOUT', 10),
        from_addr=config['FROM_ADDR'],
        email_password=config['EMAIL_PASSWORD'],
        to_addrs=config['TO_ADDRS']
    )
    kwargs['to_retry'] = True
    kwargs['subject'] = 'Email notice enabled #scrapydweb'
    kwargs['content'] = json_dumps(dict(FROM_ADDR=config['FROM_ADDR'], TO_ADDRS=config['TO_ADDRS']))

    printf("Trying to send email (smtp_connection_timeout=%s)..." % config.get('SMTP_CONNECTION_TIMEOUT', 10))
    result = send_email(**kwargs)
    if not result:
        print('')
        print(json_dumps(kwargs, sort_keys=False))
    assert result, "Fail to send email. Modify the email settings above or pass in the argument '--disable_email'"

    printf("Email notice enabled")


def init_subprocess(config):
    if config.get('ENABLE_LOGPARSER', True):
        config['LOGPARSER_PID'] = init_logparser(config)
    else:
        config['LOGPARSER_PID'] = None

    if config.get('ENABLE_EMAIL', True):
        config['POLL_PID'] = init_poll(config)
    else:
        config['POLL_PID'] = None
