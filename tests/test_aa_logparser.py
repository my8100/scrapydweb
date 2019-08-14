# coding: utf-8
import io
import json
import os

from flask import url_for

from scrapydweb.utils.check_app_config import check_app_config
from scrapydweb.views.files.log import REPORT_KEYS_SET
from tests.utils import cst, req, replace_file_content, sleep


# http://127.0.0.1:5000/1/log/stats/ScrapydWeb_demo/test/ScrapydWeb_demo/
# id="finish_reason">finished<
# NO refresh_button

# http://127.0.0.1:5000/1/log/stats/ScrapydWeb_demo/test/ScrapydWeb_demo_unfinished/
# id="finish_reason">N/A<
# <a id="refresh_button" class="button danger" href="javascript:location.reload(true);"
# onclick="showLoader();">Click to refresh</a>
# var by = 'ScrapydWeb';
# var click = 'click to hard reparse (SLOW)';
# my$('#refresh_button').innerHTML = "Parsed by " + by +
def test_stats_with_logparser_disabled(app, client):
    kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_JOBID)
    req(app, client, view='log', kws=kws,
        ins=["Using local logfile:", 'id="finish_reason">finished<'], nos='refresh_button')

    kws['job'] = cst.DEMO_UNFINISHED_LOG.split('.')[0]
    ins = ['id="finish_reason">N/A<', '<a id="refresh_button"', "var by = 'ScrapydWeb';"]
    req(app, client, view='log', kws=kws, ins=ins)


def test_enable_logparser(app, client):
    def json_loads_from_file(path):
        with io.open(path, 'r', encoding='utf-8') as f:
            return json.loads(f.read())

    # In conftest.py: ENABLE_LOGPARSER=False
    assert not os.path.exists(app.config['STATS_JSON_PATH'])
    assert not os.path.exists(app.config['DEMO_JSON_PATH'])
    app.config['ENABLE_LOGPARSER'] = True
    app.config['ENABLE_MONITOR'] = False

    # ['username:password@127.0.0.1:6800', ]
    app.config['SCRAPYD_SERVERS'] = app.config['_SCRAPYD_SERVERS']
    check_app_config(app.config)

    logparser_pid = app.config['LOGPARSER_PID']
    assert isinstance(logparser_pid, int) and logparser_pid > 0
    assert app.config['POLL_PID'] is None
    req(app, client, view='settings', kws=dict(node=1), ins='logparser_pid: %s' % logparser_pid)

    sleep()

    stats_json = json_loads_from_file(app.config['STATS_JSON_PATH'])
    assert stats_json['logparser_version'] == cst.LOGPARSER_VERSION
    assert cst.DEMO_JOBID in stats_json['datas'][cst.PROJECT][cst.SPIDER]
    demo_json = json_loads_from_file(app.config['DEMO_JSON_PATH'])
    assert demo_json['runtime'] == '0:01:08'
    assert demo_json['finish_reason'] == 'finished'
    assert demo_json['logparser_version'] == cst.LOGPARSER_VERSION


def test_stats_with_logparser_enabled(app, client):
    flash_logparser_version = 'LogParser v%s' % cst.LOGPARSER_VERSION

    kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_JOBID)
    req(app, client, view='log', kws=kws,
        ins=[flash_logparser_version, 'id="finish_reason">finished<'], nos='refresh_button')

    # <a class="button danger" href="/1/log/stats/ScrapydWeb_demo/test/ScrapydWeb_demo_unfinished/?realtime=True"
    # onclick="showLoader();">Realtime version</a>
    demo_unfinished_log_without_ext = cst.DEMO_UNFINISHED_LOG.split('.')[0]
    kws['job'] = demo_unfinished_log_without_ext
    with app.test_request_context():
        url_realtime = url_for('log', node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER,
                               job=demo_unfinished_log_without_ext, realtime='True')
    ins = [flash_logparser_version, '<a id="refresh_button"', "javascript:location.reload(true);",
           url_realtime, ">Realtime version</a>", 'id="finish_reason">N/A<', "var by = 'LogParser';"]
    req(app, client, view='log', kws=kws, ins=ins)

    # <a class="button safe" href="/1/log/stats/ScrapydWeb_demo/test/ScrapydWeb_demo_unfinished/"
    # onclick="showLoader();">Cached version</a>
    kws['realtime'] = 'True'
    with app.test_request_context():
        url_cached = url_for('log', node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER,
                             job=demo_unfinished_log_without_ext)
    nos = flash_logparser_version
    ins = [url_cached, ">Cached version</a>", '<a id="refresh_button"', "javascript:location.reload(true);",
           'id="finish_reason">N/A<', "var by = 'ScrapydWeb';"]
    req(app, client, view='log', kws=kws, nos=nos, ins=ins)


# Note that DEMO_JSON is used in test_log.py, avoid removing it
def test_stats_with_file_deleted(app, client):
    tab = ">Log analysis</li>"
    old = '"logparser_version": "%s",' % cst.LOGPARSER_VERSION
    new = '"logparser_version": "0.0.0",'

    def rename(name, restore=False):
        if restore:
            os.rename(name + '.bak', name)
        else:
            os.rename(name, name + '.bak')

    kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_JOBID)
    req(app, client, view='log', kws=kws, ins=["Using local stats: LogParser v%s" % cst.LOGPARSER_VERSION, tab])

    # Make IS_LOCAL_SCRAPYD_SERVER False to test request_stats_by_logparser() Pass
    app.config['LOCAL_SCRAPYD_SERVER'] = app.config['SCRAPYD_SERVERS'][-1]
    kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_JOBID)
    # LogParser v0.8.1, last updated at xxx, http://127.0.0.1:6800/logs/ScrapydWeb_demo/test/ScrapydWeb_demo.json
    req(app, client, view='log', kws=kws, ins=["LogParser v%s, last updated at" % cst.LOGPARSER_VERSION, tab],
        nos="Using local stats:")
    # Get report
    kws_ = dict(kws)
    kws_['opt'] = 'report'
    jskeys = list(REPORT_KEYS_SET)
    req(app, client, view='log', kws=kws_, jskws=dict(status=cst.OK, from_memory=False), jskeys=jskeys)
    req(app, client, view='log', kws=kws_, jskws=dict(status=cst.OK, from_memory=True), jskeys=jskeys)
    kws_['project'] = cst.FAKE_PROJECT
    req(app, client, view='log', kws=kws_, jskws=dict(status=cst.ERROR))

    app.config['LOCAL_SCRAPYD_SERVER'] = app.config['SCRAPYD_SERVERS'][0]

    # Mismatching logparser_version in ScrapydWeb_demo.json in logs
    replace_file_content(app.config['DEMO_JSON_PATH'], old, new)
    req(app, client, view='log', kws=kws,
        ins=["Mismatching logparser_version 0.0.0 in local stats",
             "pip install --upgrade logparser", "Using local logfile:", tab])
    replace_file_content(app.config['DEMO_JSON_PATH'], new, old)

    # delete ScrapydWeb_demo.json in logs
    # os.remove(app.config['DEMO_JSON_PATH'])
    rename(app.config['DEMO_JSON_PATH'])
    kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_JOBID)
    req(app, client, view='log', kws=kws,
        ins=["pip install logparser", "Or wait until LogParser parses the log.", "Using local logfile:", tab])

    app.config['ENABLE_LOGPARSER'] = True  # Test flash content for local scrapyd server
    kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_JOBID)
    req(app, client, view='log', kws=kws,
        ins=["got code 404, wait until LogParser parses the log.", tab], nos="pip install logparser")

    # delete ScrapydWeb_demo.log in logs
    rename(app.config['DEMO_LOG_PATH'])
    kws = dict(node=1, opt='utf8', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_JOBID)
    req(app, client, view='log', kws=kws,
        ins=["fail - ScrapydWeb", "404 - No Such Resource", "Fail to request logfile", "with extensions"])

    kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_JOBID)
    req(app, client, view='log', kws=kws, ins=["Using backup stats: LogParser v%s" % cst.LOGPARSER_VERSION, tab])

    # Mismatching logparser_version in ScrapydWeb_demo.json in data/stats
    replace_file_content(app.config['BACKUP_DEMO_JSON_PATH'], old, new)
    req(app, client, view='log', kws=kws,
        ins=["fail - ScrapydWeb", "404 - No Such Resource", "Fail to request logfile", "with extensions",
             "Mismatching logparser_version 0.0.0 in backup stats"])
    replace_file_content(app.config['BACKUP_DEMO_JSON_PATH'], new, old)

    # delete ScrapydWeb_demo.json in data/stats
    rename(app.config['BACKUP_DEMO_JSON_PATH'])
    kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_JOBID)
    req(app, client, view='log', kws=kws,
        ins=["fail - ScrapydWeb", "404 - No Such Resource", "Fail to request logfile", "with extensions"])

    for filepath in ['DEMO_JSON_PATH', 'DEMO_LOG_PATH', 'BACKUP_DEMO_JSON_PATH']:
        rename(app.config[filepath], restore=True)
