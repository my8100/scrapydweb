# coding: utf8
import os
import sys
from shutil import rmtree
import re

from ..vars import ALLOWED_SCRAPYD_LOG_EXTENSIONS, CACHE_PATH, EMAIL_TRIGGER_KEYS
from .utils import printf, json_dumps
from .send_email import send_email


pattern_email = re.compile(r'^[^@]+@[^@]+\.[^@]+$')


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
    except (ValueError, AssertionError):
        sys.exit("SCRAPYDWEB_PORT should be a positive integer. Current value: %s" % SCRAPYDWEB_PORT)

    check_assert('DISABLE_AUTH', True, bool)
    if not config.get('DISABLE_AUTH', True):
        # May be 0 from config file
        check_assert('USERNAME', '', str, non_empty=True)
        check_assert('PASSWORD', '', str, non_empty=True)
        printf("Basic auth enabled with USERNAME/PASSWORD: '%s'/'%s'" % (config['USERNAME'], config['PASSWORD']))

    # Scrapy
    check_assert('SCRAPY_PROJECTS_DIR', '', str)
    SCRAPY_PROJECTS_DIR = config.get('SCRAPY_PROJECTS_DIR', '')
    if SCRAPY_PROJECTS_DIR:
        if not os.path.isdir(SCRAPY_PROJECTS_DIR):
            sys.exit("!!! SCRAPY_PROJECTS_DIR NOT found: %s" % SCRAPY_PROJECTS_DIR)
        else:
            printf("Using SCRAPY_PROJECTS_DIR: %s" % SCRAPY_PROJECTS_DIR)

    # Scrapyd
    # print(config.get('SCRAPYD_SERVERS'))  # Checked in the preceding update_app_config()
    check_assert('SCRAPYD_LOGS_DIR', '', str)
    SCRAPYD_LOGS_DIR = config.get('SCRAPYD_LOGS_DIR', '')
    if SCRAPYD_LOGS_DIR:
        if not os.path.isdir(SCRAPYD_LOGS_DIR):
            sys.exit("!!! SCRAPYD_LOGS_DIR NOT found: %s" % SCRAPYD_LOGS_DIR)
        else:
            printf("Using SCRAPYD_LOGS_DIR: %s" % SCRAPYD_LOGS_DIR)

    check_assert('SCRAPYD_LOG_EXTENSIONS', ALLOWED_SCRAPYD_LOG_EXTENSIONS, list, non_empty=True, containing_type=str)
    SCRAPYD_LOG_EXTENSIONS = config.get('SCRAPYD_LOG_EXTENSIONS', ALLOWED_SCRAPYD_LOG_EXTENSIONS)
    assert all([not i or i.startswith('.') for i in SCRAPYD_LOG_EXTENSIONS]), \
        ("SCRAPYD_LOG_EXTENSIONS should be a list like %s. "
         "Current value: %s" % (ALLOWED_SCRAPYD_LOG_EXTENSIONS, SCRAPYD_LOG_EXTENSIONS))
    printf("Locating scrapy log with SCRAPYD_LOG_EXTENSIONS: %s" % SCRAPYD_LOG_EXTENSIONS)

    # Page Display
    check_assert('SHOW_SCRAPYD_ITEMS', True, bool)
    check_assert('SHOW_DASHBOARD_JOB_COLUMN', False, bool)
    check_assert('DASHBOARD_RELOAD_INTERVAL', 300, int)
    check_assert('DAEMONSTATUS_REFRESH_INTERVAL', 10, int)

    # HTML Caching
    check_assert('DISABLE_CACHE', False, bool)
    if not config.get('DISABLE_CACHE', False):
        check_assert('CACHE_ROUND_INTERVAL', 300, int, allow_zero=False)
        check_assert('CACHE_REQUEST_INTERVAL', 10, int, allow_zero=False)

    check_assert('DELETE_CACHE', False, bool)
    if config.get('DELETE_CACHE', False):
        if os.path.isdir(CACHE_PATH):
            rmtree(CACHE_PATH, ignore_errors=True)
            printf("Cached HTML files of Log and Stats page deleted")
        else:
            printf("Cache dir NOT found: %s" % CACHE_PATH, warn=True)

    # Email Notice
    check_assert('DISABLE_EMAIL', True, bool)
    if not config.get('DISABLE_EMAIL', True):
        check_assert('SMTP_SERVER', '', str, non_empty=True)
        check_assert('SMTP_PORT', 0, int, allow_zero=False)
        check_assert('SMTP_OVER_SSL', False, bool)
        check_assert('SMTP_CONNECTION_TIMEOUT', 10, int, allow_zero=False)

        check_assert('FROM_ADDR', '', str, non_empty=True)
        FROM_ADDR = config['FROM_ADDR']
        assert pattern_email.search(FROM_ADDR), \
            "FROM_ADDR should contain '@', like 'username@gmail.com'. Current value: %s" % FROM_ADDR
        check_assert('EMAIL_PASSWORD', '', str, non_empty=True)
        check_assert('TO_ADDRS', [], list, non_empty=True, containing_type=str)
        TO_ADDRS = config['TO_ADDRS']
        assert all([pattern_email.search(i) for i in TO_ADDRS]), \
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

        check_assert('ON_JOB_RUNNING_INTERVAL', 0, int)
        check_assert('ON_JOB_FINISHED', False, bool)

        for k in EMAIL_TRIGGER_KEYS:
            check_assert('LOG_%s_THRESHOLD' % k, 0, int)
            check_assert('LOG_%s_TRIGGER_STOP' % k, False, bool)
            check_assert('LOG_%s_TRIGGER_FORCESTOP' % k, False, bool)

        check_email(config)

    # System
    check_assert('DEBUG', False, bool)
    if config.get('DEBUG', False):
        printf("It's not recommended to run in debug mode, set 'DEBUG = False' instead", warn=True)
    check_assert('VERBOSE', False, bool)


def check_email(config):
    assert not config.get('DISABLE_CACHE', False), \
        ("In order to enable 'Email Notice', you have to enable 'HTML Caching' by setting "
         "'DISABLE_CACHE = False' first,\nalso, don't pass in the argument '--disable_cache'")

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
    kwargs['subject'] = 'ScrapydWeb sender %s' % config['FROM_ADDR']
    kwargs['content'] = 'ScrapydWeb recipients %s' % config['TO_ADDRS']

    printf("Trying to send email (smtp_connection_timeout=%s)..." % config.get('SMTP_CONNECTION_TIMEOUT', 10))
    result = send_email(**kwargs)
    if not result:
        print('')
        print(json_dumps(kwargs, sort_keys=False))
    assert result, "Fail to send email. Modify the email settings above or pass in the argument '--disable_email'"

    printf("Email notice enabled")
