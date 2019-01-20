# coding: utf8
import io
import json
import os

from flask import url_for

from scrapydweb.utils.check_app_config import check_app_config
from tests.utils import cst, req, sleep


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
    kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_LOG.split('.')[0])
    req(app, client, view='log', kws=kws,
        ins='id="finish_reason">finished<', nos='refresh_button')

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
    app.config['ENABLE_EMAIL'] = False
    check_app_config(app.config)
    logparser_pid = app.config['LOGPARSER_PID']
    assert isinstance(logparser_pid, int) and logparser_pid > 0
    assert app.config['POLL_PID'] is None
    req(app, client, view='settings', kws=dict(node=1), ins='logparser_pid: %s' % logparser_pid)

    sleep()

    stats_json = json_loads_from_file(app.config['STATS_JSON_PATH'])
    assert stats_json['logparser_version'] == cst.LOGPARSER_VERSION
    assert cst.DEMO_LOG.split('.')[0] in stats_json['datas'][cst.PROJECT][cst.SPIDER]
    demo_json = json_loads_from_file(app.config['DEMO_JSON_PATH'])
    assert demo_json['elapsed'] == '0:01:08'
    assert demo_json['finish_reason'] == 'finished'
    assert demo_json['logparser_version'] == cst.LOGPARSER_VERSION


def test_stats_with_logparser_enabled(app, client):
    flash_logparser_version = 'LogParser v%s' % cst.LOGPARSER_VERSION

    kws = dict(node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.DEMO_LOG.split('.')[0])
    req(app, client, view='log', kws=kws,
        ins=[flash_logparser_version, 'id="finish_reason">finished<'], nos='refresh_button')

    # <a class="button danger" href="/1/log/stats/ScrapydWeb_demo/test/ScrapydWeb_demo_unfinished/?realtime=True"
    # onclick="showLoader();">Realtime version</a>
    demo_unfinished_log_without_ext = cst.DEMO_UNFINISHED_LOG.split('.')[0]
    kws['job'] = demo_unfinished_log_without_ext
    with app.test_request_context():
        url_realtime = url_for('log', node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER,
                               job=demo_unfinished_log_without_ext, realtime='True')
    ins = [flash_logparser_version, '<a id="refresh_button"', 'javascript:location.reload(true);',
           url_realtime, '>Realtime version</a>', 'id="finish_reason">N/A<', "var by = 'LogParser';"]
    req(app, client, view='log', kws=kws, ins=ins)

    # <a class="button safe" href="/1/log/stats/ScrapydWeb_demo/test/ScrapydWeb_demo_unfinished/"
    # onclick="showLoader();">Cached version</a>
    kws['realtime'] = 'True'
    with app.test_request_context():
        url_cached = url_for('log', node=1, opt='stats', project=cst.PROJECT, spider=cst.SPIDER,
                             job=demo_unfinished_log_without_ext)
    nos = flash_logparser_version
    ins = [url_cached, '>Cached version</a>', '<a id="refresh_button"', 'javascript:location.reload(true);',
           'id="finish_reason">N/A<', "var by = 'ScrapydWeb';"]
    req(app, client, view='log', kws=kws, nos=nos, ins=ins)
