# coding: utf-8
import platform
import re

from scrapy import __version__ as scrapy_version

from tests.utils import cst, req, sleep, switch_scrapyd, upload_file_deploy


NODE = 2
FILENAME = '%s_%s_%s.pickle' % (cst.PROJECT, cst.VERSION, cst.SPIDER)
KEY = '/'.join([cst.PROJECT, cst.SPIDER, cst.JOBID])
run_data = {
    '1': 'on',
    '2': 'on',
    'checked_amount': '2',
    'filename': FILENAME
}
run_data_single_scrapyd = {
    '1': 'on',
    'checked_amount': '1',
    'filename': FILENAME
}


# Multinode Run Spider button in deploy results page
# Multinode Run Spider button in servers page
def test_schedule_from_post(app, client):
    text, __ = req(app, client, view='schedule', kws=dict(node=NODE), data={'1': 'on', '2': 'on'})
    assert (re.search(r'id="checkbox_1".*?checked.*?/>', text, re.S)
            and re.search(r'id="checkbox_2".*?checked.*?/>', text, re.S))


# CHECK first to generate xx.pickle for RUN
def test_check(app, client):
    upload_file_deploy(app, client, filename='ScrapydWeb_demo.egg', project=cst.PROJECT, redirect_project=cst.PROJECT)
    data = dict(
        project=cst.PROJECT,
        _version=cst.VERSION,
        spider=cst.SPIDER,
        jobid=cst.JOBID,
        additional="-d setting=LOGSTATS_INTERVAL=10"  # For the test_telnet_in_stats() below

    )
    req(app, client, view='schedule.check', kws=dict(node=NODE), data=data,
        jskws=dict(filename=FILENAME))


def test_run(app, client):
    node = 1

    req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data,
        ins=['run results - ScrapydWeb', 'id="checkbox_1"', 'id="checkbox_2"', 'onclick="passToServers();"'])

    # test handle_unique_constraint() in jobs.py
    sleep()
    req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data_single_scrapyd,
        ins=['run results - ScrapydWeb', 'id="checkbox_1"', 'onclick="passToServers();"'], nos='id="checkbox_2"')
    keep_text = ''
    for times in [1, 2]:
        __, js = req(app, client, view='api', kws=dict(node=node, opt='listjobs', project=cst.PROJECT))
        if js['pending']:
            final_pending_job = js['pending'][-1]
            assert final_pending_job['id'] == cst.JOBID
            first_job = js['running'][-1]
            first_job_start = first_job['start_time'][:19]
            # Ignore seen pending job: ScrapydWeb_demo/test/2018-01-01T01_01_02
            flash = "Ignore seen pending job: %s" % KEY
            ins = ["Vue.extend(Main)", "start: '%s'," % first_job_start]
            nos = ['class="table wrap"', "Ignore seen running job"]
            text, __ = req(app, client, view='jobs', kws=dict(node=node, style='database'))
            try:
                if times == 1:
                    assert flash in text
                else:
                    assert flash not in text
                for i in ins:
                    assert i in text
                for n in nos:
                    assert n not in text
            except AssertionError:
                # the response containS 'Ignore seen running' instead
                keep_text = text
                break
        else:
            break

    sleep()
    __, js = req(app, client, view='api', kws=dict(node=node, opt='listjobs', project=cst.PROJECT))
    first_job = js['running'][-2]
    first_job_start = first_job['start_time'][:19]
    second_job = js['running'][-1]
    second_job_start = second_job['start_time'][:19]
    assert first_job['id'] == second_job['id'] == cst.JOBID
    # TODO: For compatibility with Debian?! Running job with same key is not ordered by start ASC?!
    # assert second_job_start > first_job_start
    # Ignore seen running job: ScrapydWeb_demo/test/2018-01-01T01_01_02, started at 2019-03-01 20:27:22
    flash = "Ignore seen running job: %s, started at %s" % (KEY, first_job_start)
    if keep_text:
        text = keep_text
    else:
        text, __ = req(app, client, view='jobs', kws=dict(node=node, style='database'))
    for i in [flash, "Vue.extend(Main)", "start: '%s'," % second_job_start]:
        assert i in text
    for n in ['class="table wrap"', "start: '%s'," % first_job_start]:
        assert n not in text
    # flash only once
    req(app, client, view='jobs', kws=dict(node=node, style='database'),
        ins=["Vue.extend(Main)", "start: '%s'," % second_job_start],
        nos=[flash, 'class="table wrap"', "start: '%s'," % first_job_start])

    for i in range(2):
        req(app, client, view='api',
            kws=dict(node=node, opt='forcestop', project=cst.PROJECT, version_spider_job=cst.JOBID))
    sleep()
    __, js = req(app, client, view='api', kws=dict(node=node, opt='listjobs', project=cst.PROJECT))
    last_but_two_finished_job = js['finished'][-2]
    last_but_two_finished_job_start = last_but_two_finished_job['start_time'][:19]
    last_finished_job = js['finished'][-1]
    last_finished_job_start = last_finished_job['start_time'][:19]
    assert last_but_two_finished_job['id'] == last_finished_job['id'] == cst.JOBID
    # Ignore seen finished job: ScrapydWeb_demo/test/2018-01-01T01_01_02, started at 2019-03-01 20:27:22
    flash = "Ignore seen finished job: %s, started at %s" % (KEY, last_but_two_finished_job_start)
    req(app, client, view='jobs', kws=dict(node=node, style='database'),
        ins=[flash, "Vue.extend(Main)", "start: '%s'," % last_finished_job_start],
        nos=['class="table wrap"', "start: '%s'," % last_but_two_finished_job_start])
    # flash only once
    req(app, client, view='jobs', kws=dict(node=node, style='database'),
        ins=["Vue.extend(Main)", "start: '%s'," % last_finished_job_start],
        nos=[flash, 'class="table wrap"', "start: '%s'," % last_but_two_finished_job_start])


# Note that in LogParser is enabled in test_enable_logparser(), with PARSE_ROUND_INTERVAL defaults to 10.
# And LOGSTATS_INTERVAL is set to 10 in test_check() above.
# This test would fail if Scrapy >= 1.5.2 since telnet console now requires username and password
# https://doc.scrapy.org/en/latest/news.html#scrapy-1-5-2-2019-01-22
def test_telnet_in_stats(app, client):
    node = 1
    desktop_ins = [">Log analysis</li>", ">Log categorization</li>", ">View log</li>", ">Progress visualization</li>"]
    mobile_ins = [">Analysis</li>", ">Categories</li>", ">Charts</li>", ">Logs</li>"]
    telnet_ins = [">Crawler.stats</li>", "<td>datetime.datetime(",
                  ">Crawler.engine</li>", "<th>engine.has_capacity()</th>", "<td>telnet</td>"]
    telnet_nos = ["CRITICAL: Unhandled Error", "telnet.OptionRefused"]
    req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data, ins="run results - ScrapydWeb")

    kws = dict(node=node, opt='stats', project=cst.PROJECT, spider=cst.SPIDER, job=cst.JOBID)
    for i in range(1, 4):
        sleep(10)
        print(i * 10)
        text, __ = req(app, client, view='log', kws=kws)
        if desktop_ins[-1] in text and telnet_ins[-1] in text:
            print("Found: %s %s" % (desktop_ins[-1], telnet_ins[-1]))
            break
    # test jobs POST data={} to save pages and items in database
    __, js = req(app, client, view='jobs', kws=dict(node=node), data={})
    assert isinstance(js[KEY]['pages'], int)  # and js[KEY]['pages'] > 0

    # Linux-5.0.9-301.fc30.x86_64-x86_64-with-fedora-30-Thirty'
    if (platform.system() == 'Windows' or 'fedora' in platform.platform()) and scrapy_version > '1.5.1':
        print("telnet not available for scrapy_version: %s" % scrapy_version)
        telnet_ins = []

    req(app, client, view='log', kws=kws, ins=desktop_ins + telnet_ins, nos=telnet_nos)

    kws.update(ui='mobile')
    req(app, client, view='log', kws=kws,
        ins=mobile_ins + telnet_ins, nos=telnet_nos, mobileui=True)

    req(app, client, view='api',
        kws=dict(node=node, opt='forcestop', project=cst.PROJECT, version_spider_job=cst.JOBID))


def test_pending_jobs(app, client):
    node = 1
    for i in range(2):
        req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data, ins="run results - ScrapydWeb")
    req(app, client, view='jobs', kws=dict(node=node, style='database'),
        ins="Vue.extend(Main)", nos='class="table wrap"')
    sleep()
    for i in range(2):
        req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data, ins="run results - ScrapydWeb")
    req(app, client, view='jobs', kws=dict(node=node, style='database'),
        ins="Vue.extend(Main)", nos='class="table wrap"')
    sleep()
    req(app, client, view='jobs', kws=dict(node=node, style='database'),
        ins=["Ignore seen running job: %s, started at" % KEY, "Vue.extend(Main)"], nos='class="table wrap"')
    for i in range(4):
        req(app, client, view='api',
            kws=dict(node=node, opt='forcestop', project=cst.PROJECT, version_spider_job=cst.JOBID))


def test_run_fail(app, client):
    switch_scrapyd(app)
    req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data, ins='Multinode schedule terminated')


def test_schedule_xhr(app, client):
    req(app, client, view='schedule.xhr',
        kws=dict(node=NODE, filename=FILENAME),
        jskws=dict(status=cst.ERROR))
