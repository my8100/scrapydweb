# coding: utf-8
"""
REF: test_schedule_single_scrapyd.py
"""
import re

from flask import url_for
from six.moves.urllib.parse import unquote_plus
from tzlocal import get_localzone

from tests.utils import cst, req_single_scrapyd, sleep, upload_file_deploy


NODE = 1
NAME = u"""Chinese' "中文"""
VALUE = u"""Test' "测试"""
FILENAME = '%s_%s_%s.pickle' % (cst.PROJECT, cst.VERSION, cst.SPIDER)
FILENAME_DV = '%s_%s_%s.pickle' % (cst.PROJECT, 'default-the-latest-version', cst.SPIDER)
TITLE = '/'.join([cst.PROJECT, cst.VERSION, cst.SPIDER, cst.JOBID])
TITLE_DV = '/'.join([cst.PROJECT, cst.DEFAULT_LATEST_VERSION, cst.SPIDER, cst.JOBID])
metadata = {}
DATA = {}
DATA_DV = {}


# check POST default "action": "add"
def test_check_with_task(app, client):
    DATA.update(dict(
        project=cst.PROJECT,
        _version=cst.VERSION,
        spider=cst.SPIDER,
        jobid=cst.JOBID,
        USER_AGENT='iPhone',
        ROBOTSTXT_OBEY='True',
        COOKIES_ENABLED='False',
        CONCURRENT_REQUESTS='5',
        DOWNLOAD_DELAY='10',
        additional=("-d setting=CLOSESPIDER_PAGECOUNT=20\r\n"
                    u"-d arg1=%s\r\n"
                    "-d setting=CLOSESPIDER_TIMEOUT=120") % VALUE
    ))
    DATA.update(dict(
        year='2036',
        month='12',
        day='31',
        week='1',   # datetime.date(2036, 12, 31).isocalendar()[1]
        # day_of_week=['*'],
        day_of_week='mon-fri,sun',  # From browser: "*" | "*,mon-fri" | ""
        hour='2',
        minute='3',
        second='4',

        # start_date='',
        # end_date='',
        start_date='2019-01-01 00:00:00',
        end_date='2036-12-31 23:59:59',

        timezone='Asia/Shanghai',  # str(get_localzone())   'Asia/Shanghai'
        jitter='0',
        misfire_grace_time='600',
        coalesce='True',
        max_instances='1',

        task_id='0',
        action='add_fire',
        trigger='cron',
        name=NAME,
        replace_existing='True',
    ))
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=NODE), data=DATA,
                       jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))

    DATA_DV.update(dict(DATA))
    DATA_DV.update(_version=cst.DEFAULT_LATEST_VERSION)
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=NODE), data=DATA_DV,
                       jskws=dict(filename=FILENAME_DV),
                       nos="-d _version=")


def check_dumped_task_data(js, version=cst.VERSION, day_of_week='mon-fri,sun'):
    data = js['data']
    settings_dict = dict(
        ROBOTSTXT_OBEY=True,
        COOKIES_ENABLED=False,
        CONCURRENT_REQUESTS=5,
        DOWNLOAD_DELAY=10,
        CLOSESPIDER_PAGECOUNT=20,
        CLOSESPIDER_TIMEOUT=120
    )

    trigger_data = dict(
        year='2036',
        month='12',
        day='31',
        week='1',
        day_of_week=day_of_week,
        hour='2',
        minute='3',
        second='4',

        # start_date=None,
        # end_date=None,
        start_date='2019-01-01 00:00:00+08:00',
        end_date='2036-12-31 23:59:59+08:00',

        timezone='Asia/Shanghai',  # str(get_localzone())   'Asia/Shanghai'
        jitter=0,
    )
    assert data['id'] == js['task_id']
    assert isinstance(data['id'], int)
    # assert data['name'] is None
    assert data['name'] == NAME
    assert data['trigger'] == 'cron'
    assert data['create_time']
    assert data['update_time']

    assert data['project'] == cst.PROJECT
    assert data['version'] == version
    assert data['spider'] == cst.SPIDER
    assert data['jobid'] == cst.JOBID

    assert len(data['settings_arguments']) == 2
    assert data['settings_arguments']['arg1'] == VALUE
    assert len(data['settings_arguments']['setting']) == len(settings_dict) + 1
    assert 'USER_AGENT=Mozilla/5.0 (iPhone' in str(data['settings_arguments'])
    for k, v in settings_dict.items():
        assert '%s=%s' % (k, v) in data['settings_arguments']['setting']
    assert data['selected_nodes'] == [1]

    assert data['apscheduler_job']['trigger'] == trigger_data
    for k, v in trigger_data.items():
        if k in ['start_date', 'end_date']:
            assert v.startswith(data[k])
        else:
            assert data[k] == v

    assert data['apscheduler_job']['id'] == str(js['task_id'])  # str
    assert data['apscheduler_job']['kwargs'] == dict(task_id=js['task_id'])
    assert data['apscheduler_job']['misfire_grace_time'] == data['misfire_grace_time'] == 600
    assert data['apscheduler_job']['coalesce'] is True
    assert data['coalesce'] == 'True'
    assert data['apscheduler_job']['max_instances'] == data['max_instances'] == 1
    assert data['apscheduler_job']['next_run_time'] == "2036-12-31 02:03:04+08:00"


def test_enable_disable_scheduler(app, client):
    flash = "test flash in url"
    tip = "Click the DISABLED button to enable the scheduler for timer tasks"
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='enable'),
                       ins='STATE_RUNNING', nos='STATE_PAUSED')
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE), nos=tip)

    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='disable'),
                       ins='STATE_PAUSED', nos='STATE_RUNNING')
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, flash=flash), ins=[flash, tip])

    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='enable'),
                       ins='STATE_RUNNING', nos='STATE_PAUSED')
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE), nos=tip)


# You should be redirected automatically to target URL: <a href="/1/tasks/?flash=Add+task+%239+%28task_9%29+successfully
# {target} task #{task_id} ({task_name}) successfully
def test_run_with_task(app, client):
    # ScrapydWeb_demo.egg: custom_settings = {}, also output specific settings & arguments in the log
    upload_file_deploy(app, client, filename='ScrapydWeb_demo_no_request.egg', project=cst.PROJECT,
                       redirect_project=cst.PROJECT)

    with app.test_request_context():
        metadata['location'] = url_for('tasks', node=NODE)
    # 'schedule.check' in test_check_with_task()
    text, __ = req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=NODE),
                                  data=dict(filename=FILENAME),
                                  location=metadata['location'])
    sleep()
    m = re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text))
    task_id = int(m.group(1))
    next_run_time = m.group(2)
    print("task_id: %s" % task_id)
    print("next_run_time: %s" % next_run_time)
    metadata['task_id'] = task_id
    metadata['next_run_time'] = next_run_time

    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert task_id in js['ids']
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    check_dumped_task_data(js)
    text, __ = req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE))
    jobid = re.search(r'/(task_%s_[\w-]+?)/' % task_id, text).group(1)  # extract jobid from url_stats in tasks
    print("jobid: %s" % jobid)
    metadata['jobid'] = jobid

    ins = [
        'JOB: %s' % jobid,
        'USER_AGENT: Mozilla/5.0 (iPhone',
        'ROBOTSTXT_OBEY: True',
        'COOKIES_ENABLED: False',
        'CONCURRENT_REQUESTS: 5',
        'DOWNLOAD_DELAY: 10',
        'CLOSESPIDER_TIMEOUT: 120',
        'CLOSESPIDER_PAGECOUNT: 20',
        (u'self.arg1: %s' % VALUE).replace("'", '&#39;').replace('"', '&#34;')
    ]
    # In utf8 page: <div id="log">  [test] DEBUG: self.arg1: Test&#39; &#34;测试   </pre>
    # https://stackoverflow.com/questions/2087370/decode-html-entities-in-python-string
    req_single_scrapyd(app, client, view='log',
                       kws=dict(node=NODE, opt='utf8', project=cst.PROJECT, spider=cst.SPIDER, job=jobid),
                       ins=ins)
    req_single_scrapyd(app, client, view='api',
                       kws=dict(node=NODE, opt='forcestop', project=cst.PROJECT, version_spider_job=jobid))


def test_check_tasks(app, client):
    task_id = metadata['task_id']
    jobid = metadata['jobid']
    with app.test_request_context():
        metadata['url_stats'] = url_for('log', node=NODE, opt='stats',
                                        project=cst.PROJECT, spider=cst.SPIDER, job=jobid)
        metadata['url_tasks'] = url_for('tasks', node=NODE)
        metadata['url_task_results'] = url_for('tasks', node=NODE, task_id=task_id)
        metadata['url_pause'] = url_for('tasks.xhr', node=NODE, action='pause', task_id=task_id)
        metadata['url_resume'] = url_for('tasks.xhr', node=NODE, action='resume', task_id=task_id)
        metadata['url_fire'] = url_for('tasks.xhr', node=NODE, action='fire', task_id=task_id)
        metadata['url_stop'] = url_for('tasks.xhr', node=NODE, action='remove', task_id=task_id)
        metadata['url_delete'] = url_for('tasks.xhr', node=NODE, action='delete', task_id=task_id)
        metadata['url_edit'] = url_for('schedule', node=NODE, task_id=task_id)

    ins_keys = ['url_pause', 'url_fire', 'url_stop', 'url_edit', 'url_stats', 'url_task_results']
    nos_keys = ['url_resume', 'url_delete']
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=[metadata[k] for k in ins_keys] + ["prev_run_result: '%s'," % jobid[-19:]],
                       nos=[metadata[k] for k in nos_keys])

    next_run_time_valid = "next_run_time: '2036-12-31 02:03:04+08:00',"
    next_run_time_invalid = "next_run_time: 'Click DISABLED button first. ',"
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=next_run_time_valid, nos=next_run_time_invalid)

    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='disable'),
                       ins='STATE_PAUSED', nos='STATE_RUNNING')
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=next_run_time_invalid, nos=next_run_time_valid)

    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='enable'),
                       ins='STATE_RUNNING', nos='STATE_PAUSED')
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=next_run_time_valid, nos=next_run_time_invalid)


def test_check_task_results_with_job(app, client):
    task_id = metadata['task_id']
    metadata['server'] = app.config['SCRAPYD_SERVERS'][0]  # when fail: [node 1] 127.0.0.1:5000
    text, __ = req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
                                  ins=[TITLE, metadata['url_tasks'], '[node 1] %s' % metadata['server'],
                                       "status_code: 200,", "status: 'ok',", metadata['url_stats'],
                                       "result: '%s'," % metadata['jobid'], ":total='1'"],
                                  nos=[metadata['url_task_results'], 'label="Pass count"', 'label="Server"'])

    # in the task results page: url_action: '/1/tasks/xhr/delete/5/10/',
    task_result_id = int(re.search(r'%s(\d+)/' % metadata['url_delete'], text).group(1))
    print("task_result_id: %s" % task_result_id)
    metadata['task_result_id'] = task_result_id

    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list', task_id=task_id),
                       jskws=dict(ids=[task_result_id]))

    with app.test_request_context():
        metadata['url_delete_task_result'] = url_for('tasks.xhr', node=NODE, action='delete',
                                                     task_id=task_id, task_result_id=task_result_id)
    assert metadata['url_delete_task_result'] in text


def test_check_task_job_results(app, client):
    task_id = metadata['task_id']
    task_result_id = metadata['task_result_id']

    __, js = req_single_scrapyd(app, client, view='tasks.xhr',
                                kws=dict(node=NODE, action='list', task_id=task_id, task_result_id=task_result_id))
    assert len(js['ids']) == 1

    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id, task_result_id=task_result_id),
                       ins=[TITLE, metadata['url_tasks'], metadata['url_task_results'],
                            'label="Server"', 'label="Node"', metadata['server'],
                            "status_code: 200,", "status: 'ok',", metadata['url_stats'],
                            "result: '%s'," % metadata['jobid'], ":total='1'"],
                       nos=metadata['url_delete_task_result'])


def test_check_task_not_exist(app, client):
    # edit_task
    req_single_scrapyd(app, client, view='schedule', kws=dict(node=NODE, task_id=cst.BIGINT),
                       ins=["fail - ScrapydWeb", "Task #%s not found" % cst.BIGINT])

    # dump
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=cst.BIGINT),
                       jskws=dict(data=None, status=cst.ERROR, message="Task #%s not found" % cst.BIGINT))

    # fire
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='fire', task_id=cst.BIGINT),
                       jskws=dict(status=cst.ERROR, message="apscheduler_job #%s not found" % cst.BIGINT),
                       nos=metadata['url_task_results'])

    # task_results
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=cst.BIGINT),
                       ins=["fail - ScrapydWeb", "Task #%s not found" % cst.BIGINT])

    # task_job_results
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=cst.BIGINT, task_result_id=1),
                       ins=["fail - ScrapydWeb", "Task #%s not found" % cst.BIGINT])


# TasksXhrView fire|pause|resume|remove|delete
def test_task_xhr_fire(app, client):
    task_id = metadata['task_id']
    # Note that the url_stats in the tasks page would be changed after a fire
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='fire', task_id=task_id),
                       jskws=dict(status=cst.OK, tip="Reload this page", url_jump=metadata['url_task_results']))
    sleep()
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list', task_id=task_id))
    assert len(js['ids']) == 2
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id), ins=":total='2'")


# apscheduler_job #1 after 'pause': task_1 (trigger:
# cron[year='*', month='*', day='*', week='*', day_of_week='*', hour='*', minute='0', second='0'], paused)
def test_task_xhr_pause(app, client):
    task_id = metadata['task_id']
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='pause', task_id=task_id),
                       jskws=dict(status=cst.OK, tip=", paused)"))

    ins_keys = ['url_resume', 'url_stop', 'url_edit', 'url_task_results']  # without url_stats
    nos_keys = ['url_pause', 'url_fire', 'url_delete']
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=[metadata[k] for k in ins_keys],
                       nos=[metadata[k] for k in nos_keys])
    # fire a paused task
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='fire', task_id=task_id),
                       jskws=dict(status=cst.ERROR, message="resume it first"),
                       nos=['url_jump', metadata['url_task_results']])


# task_1 (trigger: cron[year='*', month='*', day='*', week='*', day_of_week='*', hour='*', minute='0', second='0'],
# next run at: 2019-01-01 00:00:01 CST)
def test_task_xhr_resume(app, client):
    task_id = metadata['task_id']
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='resume', task_id=task_id),
                       jskws=dict(status=cst.OK, tip="next run at:"))

    ins_keys = ['url_pause', 'url_fire', 'url_stop', 'url_edit', 'url_task_results']  # without url_stats
    nos_keys = ['url_resume', 'url_delete']
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=[metadata[k] for k in ins_keys],
                       nos=[metadata[k] for k in nos_keys])


# 'Stop' button to 'remove' an apscheduler_job
def test_task_xhr_remove(app, client):
    task_id = metadata['task_id']
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='remove', task_id=task_id),
                       jskws=dict(status=cst.OK, tip="apscheduler_job #%s after 'remove': None" % task_id))
    ins_keys = ['url_delete', 'url_edit', 'url_task_results']  # without url_stats
    nos_keys = ['url_pause', 'url_resume', 'url_fire', 'url_stop']
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=[metadata[k] for k in ins_keys],
                       nos=[metadata[k] for k in nos_keys])

    # Make sure the task results is not deleted
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list', task_id=task_id))
    assert len(js['ids']) == 2
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id), ins=":total='2'")
    # handle_apscheduler_job which is not exist
    for action in ['pause', 'resume', 'remove']:
        req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action=action, task_id=task_id),
                           jskws=dict(status=cst.ERROR, message="apscheduler_job #%s not found" % task_id))
    # dump task data without apscheduler_job
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id),
                                jskws=dict(tip="apscheduler_job #%s not found" % task_id))
    assert js['data']['apscheduler_job'] is None


def test_task_xhr_delete_a_task_result(app, client):
    task_id = metadata['task_id']
    task_result_id = metadata['task_result_id']

    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list', task_id=task_id))
    assert len(js['ids']) == 2 and task_result_id in js['ids']
    req_single_scrapyd(app, client, view='tasks.xhr',
                       kws=dict(node=NODE, action='delete', task_id=task_id, task_result_id=task_result_id),
                       jskws=dict(status=cst.OK, tip="task_result #%s deleted" % task_result_id))
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list', task_id=task_id))
    assert len(js['ids']) == 1 and task_result_id not in js['ids']

    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE), ins=metadata['url_task_results'])
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
                       ins=":total='1'", nos=metadata['url_delete_task_result'])

    # delete a task result which is not exist
    req_single_scrapyd(app, client, view='tasks.xhr',
                       kws=dict(node=NODE, action='delete', task_id=task_id, task_result_id=task_result_id),
                       jskws=dict(status=cst.ERROR, message="task_result #%s not found" % task_result_id))


# remove apscheduler_job before deleting task
def test_task_xhr_delete_a_task_with_job(app, client):
    task_id = metadata['task_id']
    # 'schedule.check' in test_check_with_task()
    text, __ = req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=NODE),
                                  data=dict(filename=FILENAME_DV),
                                  location=metadata['location'])
    new_task_id = int(re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text)).group(1))
    assert new_task_id - task_id == 1

    sleep()  # Wait until the first execution finish
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=new_task_id))
    check_dumped_task_data(js, version=cst.DEFAULT_LATEST_VERSION)

    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert new_task_id in js['ids']
    tip = "apscheduler_job #{id} removed. Task #{id} deleted".format(id=new_task_id)
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=new_task_id),
                       jskws=dict(status=cst.OK, tip=tip))
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert new_task_id not in js['ids']

    message = "apscheduler_job #{id} not found. Task #{id} not found. ".format(id=new_task_id)
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=new_task_id),
                                jskws=dict(status=cst.ERROR, message=message))
    assert js['data'] is None


def test_edit_task(app, client):
    task_id = metadata['task_id']
    ins = [
        "jobid: '%s'," % cst.JOBID,
        "USER_AGENT: 'iPhone',",
        "ROBOTSTXT_OBEY: 'True',",
        "COOKIES_ENABLED: 'False',",
        "CONCURRENT_REQUESTS: '5',",
        "DOWNLOAD_DELAY: '10',",
        ("additional: '-d setting=CLOSESPIDER_PAGECOUNT=20\\r\\n-d setting=CLOSESPIDER_TIMEOUT=120\\r\\n"
         u"-d arg1=%s\\r\\n',") % (VALUE.replace("'", "\\'")),  # In HTML:  additional: '-d arg1=Test\' "测试\r\n',

        "task_id: %s," % task_id,
        "replace_existing: 'True',",
        "action: 'add_fire',",
        "trigger: 'cron',",
        u"name: '%s - edit'," % (NAME.replace("'", "\\'")),  # In HTML:  name: 'Chinese\' "中文 - edit',

        "year: '2036',",
        "month: '12',",
        "day: '31',",
        "week: '1',",
        "day_of_week: ['mon-fri', 'sun'],",
        "hour: '2',",
        "minute: '3',",
        "second: '4',",
        "start_date: '2019-01-01 00:00:00',",
        "end_date: '2036-12-31 23:59:59',",

        "timezone: 'Asia/Shanghai',",
        "jitter: 0,",
        "misfire_grace_time: 600,",
        "coalesce: 'True',",
        "max_instances: 1,",

        "expandSettingsArguments: true,",
        "expandTimerTask: true,",
        "expandTimerTaskMoreSettings: false,",
    ]
    # http://127.0.0.1:5000/1/schedule/?task_id=1
    req_single_scrapyd(app, client, view='schedule', kws=dict(node=NODE, task_id=task_id), ins=ins)


# POST data contains "task_id": "1", "replace_existing": "True",
def test_edit_to_update_a_task(app, client):
    day_of_week = 'mon-fri'
    task_id = metadata['task_id']
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    create_time = js['data']['create_time']
    update_time = js['data']['update_time']

    data = dict(DATA)
    data.update(task_id=task_id, day_of_week=day_of_week)  # modify day_of_week only
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=NODE), data=data,
                       jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))
    text, __ = req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=NODE),
                                  data=dict(filename=FILENAME),
                                  location=metadata['location'])
    assert int(re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text)).group(1)) == task_id
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert task_id in js['ids'] and (task_id + 1) not in js['ids']

    sleep()
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert js['data']['create_time'] == create_time
    assert js['data']['update_time'] > update_time
    check_dumped_task_data(js, day_of_week=day_of_week)

    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id + 1),
                       jskws=dict(data=None, status=cst.ERROR, message="Task #%s not found" % (task_id + 1)))
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=["id: %s," % task_id, "day_of_week: '%s'," % day_of_week], nos="id: %s," % (task_id + 1))


def test_edit_to_update_a_task_fail(app, client):
    day_of_week = '*'
    second = '10/*'  # ERROR INPUT
    task_id = metadata['task_id']
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    create_time = js['data']['create_time']
    update_time = js['data']['update_time']

    data = dict(DATA)
    data.update(task_id=task_id, day_of_week=day_of_week, second=second)  # modify day_of_week and second
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=NODE), data=data,
                       jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))
    text, __ = req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=NODE),
                                  data=dict(filename=FILENAME),
                                  ins=[second, "re-edit task #%s" % task_id, "fail - ScrapydWeb"])
    # re-edit task #1
    task_id_ = re.search(r're-edit task #(\d+)', text).group(1)
    assert int(task_id_) == task_id
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert task_id in js['ids'] and (task_id + 1) not in js['ids']

    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert js['data']['create_time'] == create_time
    assert js['data']['update_time'] == update_time
    check_dumped_task_data(js, day_of_week='mon-fri')  # Updated day_of_week in test_edit_to_update_a_task()

    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id + 1),
                       jskws=dict(data=None, status=cst.ERROR, message="Task #%s not found" % (task_id + 1)))
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=["id: %s," % task_id, "day_of_week: '%s'," % 'mon-fri'], nos="id: %s," % (task_id + 1))


# POST data contains "task_id": "1", "replace_existing": "False",
def test_edit_to_new_a_task(app, client):
    day_of_week = '*'
    task_id = metadata['task_id']
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    create_time = js['data']['create_time']
    update_time = js['data']['update_time']

    data = dict(DATA)
    data.update(task_id=task_id, replace_existing='False', day_of_week=day_of_week)
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=NODE), data=data,
                       jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))
    text, __ = req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=NODE),
                                  data=dict(filename=FILENAME),
                                  location=metadata['location'])
    new_task_id = int(re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text)).group(1))
    print("new_task_id: %s" % new_task_id)
    # assert new_task_id == task_id + 1
    # For compatibility with postgresql, though test_task_xhr_delete_a_task_with_job is executed before
    # https://stackoverflow.com/questions/9984196/postgresql-gapless-sequences
    assert new_task_id > task_id
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert task_id in js['ids'] and new_task_id in js['ids']

    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert js['data']['create_time'] == create_time
    assert js['data']['update_time'] == update_time
    check_dumped_task_data(js, day_of_week='mon-fri')

    sleep()
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=new_task_id))
    check_dumped_task_data(js, day_of_week=day_of_week)

    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=["id: %s," % task_id, "day_of_week: 'mon-fri',",
                            "id: %s," % new_task_id, "day_of_week: '%s'," % day_of_week])
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=new_task_id),
                       jskws=dict(status=cst.OK, tip="Task #%s deleted" % new_task_id))


# POST data contains "task_id": "1", "replace_existing": "False",
def test_edit_to_new_a_task_fail(app, client):
    day_of_week = '*'
    second = '10/*'  # ERROR INPUT
    task_id = metadata['task_id']
    data = dict(DATA)
    data.update(task_id=task_id, replace_existing='False', day_of_week=day_of_week, second=second)
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=NODE), data=data,
                       jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))
    text, __ = req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=NODE),
                                  data=dict(filename=FILENAME),
                                  ins=[day_of_week, second, "re-edit task #", "fail - ScrapydWeb"])
    # re-edit task #2
    new_task_id = int(re.search(r're-edit task #(\d+)', text).group(1))
    print("new_task_id: %s" % new_task_id)
    # For compatibility with postgresql
    assert new_task_id > task_id
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert task_id in js['ids'] and new_task_id in js['ids']

    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    check_dumped_task_data(js, day_of_week='mon-fri')
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=new_task_id))
    assert js['data']['apscheduler_job'] is None

    with app.test_request_context():
        url_pause = url_for('tasks.xhr', node=NODE, action='pause', task_id=new_task_id)
        url_resume = url_for('tasks.xhr', node=NODE, action='resume', task_id=new_task_id)
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=["id: %s," % task_id, "day_of_week: 'mon-fri',",
                            "id: %s," % new_task_id, "day_of_week: '%s'," % day_of_week, "second: '%s'," % second],
                       nos=[url_pause, url_resume])
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=new_task_id),
                       jskws=dict(status=cst.OK, tip="Task #%s deleted" % new_task_id))


def test_task_xhr_delete_a_task(app, client):
    task_id = metadata['task_id']

    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert task_id in js['ids']
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='remove', task_id=task_id),
                       jskws=dict(status=cst.OK, tip="apscheduler_job #%s after 'remove': None" % task_id))

    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert task_id in js['ids']
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=task_id),
                       jskws=dict(status=cst.OK,
                                  tip="apscheduler_job #{id} not found. Task #{id} deleted".format(id=task_id)))
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert task_id not in js['ids']

    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE), nos=metadata['url_task_results'])
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
                       ins=["fail - ScrapydWeb", "Task #%s not found" % task_id])
    # delete a task which is not exist
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=task_id),
                       jskws=dict(status=cst.ERROR, message="Task #%s not found" % task_id))


# Unrecognized expression "10/*" for field "second"
def test_add_task_fail(app, client):
    data_dv = dict(DATA_DV)
    data_dv.update(second='10/*')
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=NODE), data=data_dv,
                       jskws=dict(filename=FILENAME_DV))
    ins = ["Unrecognized expression", "10/*", "re-edit task #", "kwargs for", "task_data for", "fail - ScrapydWeb"]
    text, __ = req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=NODE),
                                  data=dict(filename=FILENAME_DV),
                                  ins=ins)
    # re-edit task #1
    task_id = int(re.search(r're-edit task #(\d+)', text).group(1))
    print("task_id: %s" % task_id)
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert task_id in js['ids']

    with app.test_request_context():
        url_pause = url_for('tasks.xhr', node=NODE, action='pause', task_id=task_id)
        url_resume = url_for('tasks.xhr', node=NODE, action='resume', task_id=task_id)

    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=["second: '10/*',", "status: 'Finished',", "prev_run_result: 'N/A',",
                            "next_run_time: '%s'," % cst.NA, "fail_times: 0,", "run_times: 0,"],
                       nos=[url_resume, url_pause])
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
                       ins=['label="Fail count"', 'label="Pass count"', ":total='0'"])
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=task_id))


# check POST  "action": "add"
def test_add_task_action_add(app, client):
    data_dv = dict(DATA_DV)
    data_dv.update(action='add', hour='*', minute='*', second='*')
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=NODE), data=data_dv,
                       jskws=dict(filename=FILENAME_DV))
    text, __ = req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=NODE),
                                  data=dict(filename=FILENAME_DV),
                                  location=metadata['location'])

    m = re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text))
    task_id = int(m.group(1))
    print("task_id: %s" % task_id)
    next_run_time = m.group(2)
    print("next_run_time: %s" % next_run_time)
    assert next_run_time == "2036-12-31 00:00:00+08:00"

    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert task_id in js['ids']
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert js['data']['apscheduler_job']['next_run_time'] == next_run_time

    with app.test_request_context():
        url_pause = url_for('tasks.xhr', node=NODE, action='pause', task_id=task_id)
        url_resume = url_for('tasks.xhr', node=NODE, action='resume', task_id=task_id)

    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=[url_pause, "prev_run_result: 'N/A',", "next_run_time: '%s'," % next_run_time,
                            "fail_times: 0,", "run_times: 0,"],
                       nos=url_resume)
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
                       ins=[TITLE_DV, 'label="Pass count"', ":total='0'"])
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id, task_result_id=cst.BIGINT),
                       ins=[TITLE_DV, 'label="Server"', ":total='0'"])
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=task_id))


# check POST  "action": "add_pause"
def test_add_task_action_pause(app, client):
    data_dv = dict(DATA_DV)
    data_dv.update(action='add_pause', hour='1-3', minute='4-6', second='7-9')
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=NODE), data=data_dv,
                       jskws=dict(filename=FILENAME_DV))
    text, __ = req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=NODE),
                                  data=dict(filename=FILENAME_DV),
                                  location=metadata['location'])

    m = re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text))
    task_id = int(m.group(1))
    print("task_id: %s" % task_id)
    next_run_time = m.group(2)
    print("next_run_time: %s" % next_run_time)
    assert next_run_time == cst.NA

    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
    assert task_id in js['ids']
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert js['data']['apscheduler_job']['next_run_time'] is None

    with app.test_request_context():
        url_pause = url_for('tasks.xhr', node=NODE, action='pause', task_id=task_id)
        url_resume = url_for('tasks.xhr', node=NODE, action='resume', task_id=task_id)
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=[url_resume, "prev_run_result: 'N/A',", "next_run_time: '%s'," % cst.NA,
                            "fail_times: 0,", "run_times: 0,"],
                       nos=url_pause)
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
                       ins=[TITLE_DV, 'label="Pass count"', ":total='0'"])
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id, task_result_id=cst.BIGINT),
                       ins=[TITLE_DV, 'label="Server"', ":total='0'"])
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=task_id))


def test_add_task_button(app, client):
    ins = [
        "expandSettingsArguments: false,",
        "expandTimerTask: true,",
        "expandTimerTaskMoreSettings: false,",

        "jobid: '',",
        "USER_AGENT: '',",
        "ROBOTSTXT_OBEY: '',",
        "COOKIES_ENABLED: '',",
        "CONCURRENT_REQUESTS: '',",
        "DOWNLOAD_DELAY: '',",
        "additional: '-d setting=CLOSESPIDER_TIMEOUT=60\\r\\n-d setting=CLOSESPIDER_PAGECOUNT=10\\r\\n-d arg1=val1'",

        "task_id: 0,",
        "replace_existing: 'True',",
        "action: 'add_fire',",
        "trigger: 'cron',",
        "name: '',",

        "year: '*',",
        "month: '*',",
        "day: '*',",
        "week: '*',",
        "day_of_week: ['*'],",
        "hour: '*',",
        "minute: '0',",
        "second: '0',",
        "start_date: '',",
        "end_date: '',",

        "timezone: '%s'," % str(get_localzone()),
        "jitter: 0,",
        "misfire_grace_time: 600,",
        "coalesce: 'True',",
        "max_instances: 1,",
    ]
    req_single_scrapyd(app, client, view='schedule', kws=dict(node=NODE, add_task='True'), ins=ins)


def test_add_task_with_default_values(app, client):
    data = dict(DATA)
    for k in data.keys():
        if k in ['jitter', 'misfire_grace_time', 'max_instances']:
            data[k] = 'invalid int'
        elif k not in ['project', '_version', 'spider', 'trigger']:  # if not request.form.get('trigger'): return
            data[k] = ''
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=NODE), data=data,
                       jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))
    text, __ = req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=NODE),
                                  data=dict(filename=FILENAME),
                                  location=metadata['location'])
    sleep()
    task_id = int(re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text)).group(1))
    print("task_id: %s" % task_id)
    __, js = req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert js['data']['settings_arguments'] == {'setting': []}
    assert js['data']['selected_nodes'] == [1]
    assert js['data']['timezone'] is None
    assert js['data']['apscheduler_job']['misfire_grace_time'] == 600
    assert js['data']['apscheduler_job']['coalesce'] is True
    assert js['data']['apscheduler_job']['max_instances'] == 1
    assert js['data']['apscheduler_job']['name'] == 'task_%s' % task_id
    assert ':00:00' in js['data']['apscheduler_job']['next_run_time']
    for k, v in js['data']['apscheduler_job']['trigger'].items():
        if k in ['start_date', 'end_date']:
            assert v is None
        elif k in ['minute', 'second']:
            assert v == '0'
        elif k == 'jitter':
            assert v == 0
        elif k == 'timezone':
            assert v == str(get_localzone())
        else:
            assert v == '*'
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=task_id))


def test_execute_task_fail(app, client):
    data = dict(DATA)
    # set_to_second
    req_single_scrapyd(app, client, view='schedule.check', kws=dict(node=NODE), data=data, set_to_second=True,
                       jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))
    text, __ = req_single_scrapyd(app, client, view='schedule.run', kws=dict(node=NODE),
                                  data=dict(filename=FILENAME),
                                  location=metadata['location'])
    task_id = int(re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text)).group(1))
    print("task_id: %s" % task_id)
    # For compatibility with postgresql
    metadata['task_id'] = task_id
    sleep(2)
    # The first execution has not finished yet
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=["id: %s," % task_id, "prev_run_result: 'FAIL 0, PASS 0',"])
    text, __ = req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
                                  ins=["fail_count: 0,", "pass_count: 0,", ":total='1'"])
    # in the task results page: url_action: '/1/tasks/xhr/delete/5/10/',
    with app.test_request_context():
        url_delete = url_for('tasks.xhr', node=NODE, action='delete', task_id=task_id)
    task_result_id = int(re.search(r'%s(\d+)/' % url_delete, text).group(1))
    print("task_result_id: %s" % task_result_id)
    sleep(28)
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE),
                       ins=["id: %s," % task_id, "prev_run_result: 'FAIL 1, PASS 0',"])
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
                       ins=["status_code: -1,", "status: 'error',", "Max retries exceeded", ":total='1'"],
                       nos="node: %s," % NODE)
    req_single_scrapyd(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id, task_result_id=task_result_id),
                       ins=["node: %s," % NODE, "status_code: -1,", "status: 'error',",
                            "Max retries exceeded", ":total='1'"])
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=task_id))


def test_history(app, client):
    task_id = metadata['task_id']
    next_run_time = metadata['next_run_time']
    req_single_scrapyd(app, client, view='tasks.history', kws=dict(),
                       ins=["timer_tasks_history.log",
                            "Add task #%s (%s) successfully" % (task_id, NAME),
                            "Added job_instance:",
                            "next run at %s" % next_run_time,
                            '"id": "%s",' % task_id,
                            '"name": "%s",' % (NAME.replace('"', '\\"')),  # "name": "Chinese' \"中文",
                            '"next_run_time": "datetime.datetime(',
                            '"trigger": "<CronTrigger',
                            "Fail to execute task #%s (%s) on node 1, would retry later" % (task_id, NAME),
                            "Max retries exceeded",
                            "Fail to execute task #%s (%s) on node 1, no more retries" % (task_id, NAME),
                            "assert js['status_code'] == 200 and js['status'] == 'ok'",
                            "Task #%s deleted" % task_id,
                            ])
