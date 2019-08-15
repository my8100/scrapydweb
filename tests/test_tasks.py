# coding: utf-8
from datetime import datetime, timedelta
import re

from flask import url_for
from six.moves.urllib.parse import unquote_plus

from tests.utils import cst, req, req_single_scrapyd, sleep, switch_scrapyd, upload_file_deploy


NODE = 2
metadata = {}
FILENAME = '%s_%s_%s.pickle' % (cst.PROJECT, cst.VERSION, cst.SPIDER)
check_data = dict(
    project=cst.PROJECT,
    _version=cst.VERSION,
    spider=cst.SPIDER,
    trigger='cron',  # if not request.form.get('trigger'): return
    hour='3'
)
run_data = {
    '1': 'on',
    '2': 'on',
    '3': 'on',  # It's out of range
    'checked_amount': '3',
    'filename': FILENAME
}
run_data_single_scrapyd = {
    '1': 'on',
    'checked_amount': '1',
    'filename': FILENAME
}


def test_check_with_task(app, client):
    req(app, client, view='schedule.check', kws=dict(node=NODE), data=check_data,
        jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))


def test_run_with_task(app, client):
    # ScrapydWeb_demo.egg: custom_settings = {}, also output specific settings & arguments in the log
    upload_file_deploy(app, client, filename='ScrapydWeb_demo_no_request.egg', project=cst.PROJECT,
                       redirect_project=cst.PROJECT)

    req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='enable'), ins='STATE_RUNNING', nos='STATE_PAUSED')

    with app.test_request_context():
        text, __ = req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data,
                       location=url_for('tasks', node=NODE))
    m = re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text))
    task_id = int(m.group(1))
    print("task_id: %s" % task_id)
    metadata['task_id'] = task_id

    __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert js['data']['selected_nodes'] == [1, 2]


def test_check_result(app, client):
    task_id = metadata['task_id']
    sleep(2)
    # The first execution has not finished yet: self.sleep_seconds_before_retry = 3
    req(app, client, view='tasks', kws=dict(node=NODE),
        ins=["id: %s," % task_id, "prev_run_result: 'FAIL 0, PASS 0',", "fail_times: 0,", "run_times: 1,"])
    text, __ = req(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
                   ins=["fail_count: 0,", "pass_count: 0,", ":total='1'"])
    with app.test_request_context():
        url_delete = url_for('tasks.xhr', node=NODE, action='delete', task_id=task_id)
    # in the task results page: url_action: '/1/tasks/xhr/delete/5/10/',
    task_result_id = int(re.search(r'%s(\d+)/' % url_delete, text).group(1))
    print("task_result_id: %s" % task_result_id)
    metadata['task_result_id'] = task_result_id
    with app.test_request_context():
        url_delete_task_result = url_for('tasks.xhr', node=NODE, action='delete',
                                         task_id=task_id, task_result_id=task_result_id)
    assert url_delete_task_result in text
    sleep(8)
    req(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id, task_result_id=task_result_id),
        ins=["node: 1,", "server: '%s'," % app.config['SCRAPYD_SERVERS'][0],
             "status_code: 200,", "status: 'ok',"])  # , ":total='1'"

    sleep(20)
    # The first execution has finished
    req(app, client, view='tasks', kws=dict(node=NODE),
        ins=["id: %s," % task_id, "prev_run_result: 'FAIL 1, PASS 1',", "fail_times: 1,", "run_times: 'FAIL 1 / 1',"])
    req(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
        ins=["fail_count: 1,", "pass_count: 1,", ":total='1'"])
    req(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id, task_result_id=task_result_id),
        ins=["node: 1,", "server: '%s'," % app.config['SCRAPYD_SERVERS'][0], "status_code: 200,", "status: 'ok',",
             "node: 2,", "server: '%s'," % app.config['SCRAPYD_SERVERS'][-1], "status_code: -1,", "status: 'error',",
             ":total='2'"])
    __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert '03:00:00' in js['data']['apscheduler_job']['next_run_time']


def test_edit_task(app, client):
    task_id = metadata['task_id']
    # http://127.0.0.1:5000/1/schedule/?task_id=1
    req(app, client, view='schedule', kws=dict(node=NODE, task_id=task_id),
        ins=["checked />[1] %s" % app.config['SCRAPYD_SERVERS'][0], "checked />[2] %s" % app.config['SCRAPYD_SERVERS'][-1]])

    check_data_ = dict(check_data)
    check_data_.update(task_id=task_id, hour='6')
    req(app, client, view='schedule.check', kws=dict(node=NODE), data=check_data_,
        jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))

    with app.test_request_context():
        metadata['location'] = url_for('tasks', node=NODE)
    text, __ = req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data_single_scrapyd,
                   location=metadata['location'])
    m = re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text))
    assert int(m.group(1)) == task_id

    __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert js['data']['selected_nodes'] == [1]

    sleep()
    req(app, client, view='tasks', kws=dict(node=NODE),
        ins=["fail_times: 1,", "run_times: 'FAIL 1 / 2',"])
    text, __ = req(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
                   ins=["fail_count: 0,", "fail_count: 1,", "pass_count: 1,", ":total='2'"])
    with app.test_request_context():
        url_delete = url_for('tasks.xhr', node=NODE, action='delete', task_id=task_id)
    # in the task results page: url_action: '/1/tasks/xhr/delete/5/10/',
    new_task_result_id = int(re.search(r'%s(\d+)/' % url_delete, text).group(1))
    print("new_task_result_id: %s" % new_task_result_id)
    req(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id, task_result_id=new_task_result_id),
        ins=["node: 1,", "server: '%s'," % app.config['SCRAPYD_SERVERS'][0],
             "status_code: 200,", "status: 'ok',", ":total='1'"])

    __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert '06:00:00' in js['data']['apscheduler_job']['next_run_time']

    req(app, client, view='schedule', kws=dict(node=NODE, task_id=task_id),
        ins="checked />[1] %s" % app.config['SCRAPYD_SERVERS'][0],
        nos="checked />[2] %s" % app.config['SCRAPYD_SERVERS'][-1])


# ['selected_nodes'] == [1] in test_edit_task() above
# switch between task_results.html and task_results_with_job.html
def test_switch_template(app, client):
    task_id = metadata['task_id']
    task_result_id = metadata['task_result_id']
    req(app, client, view='tasks.xhr',
        kws=dict(node=NODE, action='delete', task_id=task_id, task_result_id=task_result_id))
    req(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
        ins=["status_code: 200,", "status: 'ok',", ":total='1'"],
        nos=["status_code: -1,", "status: 'error',", 'label="Fail count"', 'label="Server"'])

    switch_scrapyd(app)

    req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='fire', task_id=task_id))
    sleep(2)
    req(app, client, view='tasks', kws=dict(node=NODE),
        ins=["id: %s," % task_id, "prev_run_result: 'FAIL 0, PASS 0',", "run_times: 2,"])
    req(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
        ins=['label="Fail count"', "pass_count: 0,", "fail_count: 0,", "pass_count: 1,", ":total='2'"],
        nos=['label="Server"', "status_code:", "status:"])

    sleep(28)
    req(app, client, view='tasks', kws=dict(node=NODE),
        ins=["id: %s," % task_id, "prev_run_result: 'FAIL 1, PASS 0',", "run_times: 'FAIL 1 / 2',"])
    req(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
        ins=["status_code: 200,", "status: 'ok',", "status_code: -1,", "status: 'error',", ":total='2'"],
        nos=['label="Fail count"', 'label="Server"'])

    req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=task_id))


# 1: check and run
# 9: start_time
# 10: first execute
# 11: first check result
# 15: final execute
# 19: end_time
# 21: final check result
def test_task_start_execute_end(app, client):
    while True:
        now_datetime = datetime.now()
        if now_datetime.second % 10 != 1:
            sleep(1)
        else:
            break
    start_datetime = now_datetime + timedelta(seconds=8)
    first_execute_datetime = now_datetime + timedelta(seconds=9)
    second_execute_datetime = now_datetime + timedelta(seconds=14)
    end_datetime = now_datetime + timedelta(seconds=18)
    check_data_ = dict(check_data)
    check_data_.update(action='add', hour='*', minute='*', second='*/5',
                       start_date=start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                       end_date=end_datetime.strftime("%Y-%m-%d %H:%M:%S"))
    req(app, client, view='schedule.check', kws=dict(node=NODE), data=check_data_,
        jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))
    text, __ = req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data_single_scrapyd,
                   location=metadata['location'])
    m = re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text))
    task_id = int(m.group(1))
    print("task_id: %s" % task_id)
    with app.test_request_context():
        url_pause = url_for('tasks.xhr', node=NODE, action='pause', task_id=task_id)
        url_resume = url_for('tasks.xhr', node=NODE, action='resume', task_id=task_id)
        url_delete = url_for('tasks.xhr', node=NODE, action='delete', task_id=task_id)
        url_task_results = url_for('tasks', node=NODE, task_id=task_id)
    req(app, client, view='tasks', kws=dict(node=NODE),
        ins=[url_pause, url_task_results,
             "id: %s," % task_id, "prev_run_result: '%s'," % cst.NA, "run_times: 0,"],
        nos=[url_resume, url_delete])
    __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert first_execute_datetime.strftime("%Y-%m-%d %H:%M:%S") in js['data']['apscheduler_job']['next_run_time']

    sleep(10)
    # The first execution may or may not has finished
    req(app, client, view='tasks', kws=dict(node=NODE), ins=["id: %s," % task_id, "run_times: 1,"])
    req(app, client, view='tasks', kws=dict(node=NODE),
        ins=[url_pause, url_task_results, "id: %s," % task_id, "run_times: 1,"],
        nos=[url_resume, url_delete])
    req(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id), ins=":total='1'")
    __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert second_execute_datetime.strftime("%Y-%m-%d %H:%M:%S") in js['data']['apscheduler_job']['next_run_time']

    sleep(10)
    req(app, client, view='tasks', kws=dict(node=NODE), ins=["id: %s," % task_id, "run_times: 2,"])
    req(app, client, view='tasks', kws=dict(node=NODE),
        ins=[url_delete, url_task_results, "id: %s," % task_id, "next_run_time: '%s'," % cst.NA, "run_times: 2,"],
        nos=[url_pause, url_resume])
    req(app, client, view='tasks', kws=dict(node=NODE, task_id=task_id),
        ins=["status_code: 200,", "status: 'ok',", ":total='2'"],
        nos=["status_code: -1,", "status: 'error',"])
    __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert js['data']['apscheduler_job'] is None

    req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='delete', task_id=task_id))


# Visit Timer Tasks: remove_apscheduler_job_without_task()
# execute_task():   if not task: apscheduler_job.remove()
def test_auto_remove_apscheduler_job_if_task_not_exist(app, client):
    check_data_ = dict(check_data)
    check_data_.update(action='add')

    for kind in ['visit timer tasks', 'execute_task()']:
        req(app, client, view='schedule.check', kws=dict(node=NODE), data=dict(check_data_),
            jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))
        text, __ = req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data_single_scrapyd,
                       location=metadata['location'])
        m = re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text))
        task_id = int(m.group(1))
        print("task_id: %s" % task_id)

        __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
        assert '03:00:00' in js['data']['apscheduler_job']['next_run_time']

        req(app, client, view='tasks.xhr',
            kws=dict(node=NODE, action='delete', task_id=task_id, ignore_apscheduler_job='True'))

        __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id),
                     jskws=dict(message="apscheduler_job #{id} found. Task #{id} not found".format(id=task_id)))
        assert js['data']['apscheduler_job'] == task_id

        # apscheduler_job #1 removed since task #1 not exist
        if kind == 'execute_task()':
            req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='fire', task_id=task_id))
            sleep()
        else:
            req(app, client, view='tasks', kws=dict(node=NODE),
                ins="apscheduler_job #{id} removed since task #{id} not exist".format(id=task_id),
                nos="id: %s," % task_id)
        __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id),
                     jskws=dict(
                         status=cst.ERROR,
                         message="apscheduler_job #{id} not found. Task #{id} not found".format(id=task_id)))
        assert js['data'] is None


def test_execute_task_exception(app, client):
    check_data_ = dict(check_data)
    check_data_.update(action='add')

    req(app, client, view='schedule.check', kws=dict(node=NODE), data=check_data_,
        jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))

    with app.test_request_context():
        text, __ = req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data,
                       location=url_for('tasks', node=NODE))
    m = re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text))
    task_id = int(m.group(1))
    print("task_id: %s" % task_id)

    __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
    assert js['data']['selected_nodes'] == [1, 2]

    # req_single_scrapyd would set single_scrapyd=True
    req_single_scrapyd(app, client, view='tasks.xhr', kws=dict(node=1, action='fire', task_id=task_id))

    sleep()

    req(app, client, view='tasks', kws=dict(node=1),
        ins=["id: %s," % task_id, "prev_run_result: 'FAIL 1, PASS 1',", "fail_times: 1,", "run_times: 'FAIL 1 / 1',"])
    text, __ = req(app, client, view='tasks', kws=dict(node=1, task_id=task_id),
                   ins=["fail_count: 1,", "pass_count: 1,", ":total='1'"])
    with app.test_request_context():
        url_delete = url_for('tasks.xhr', node=1, action='delete', task_id=task_id)
    # in the task results page: url_action: '/1/tasks/xhr/delete/5/10/',
    task_result_id = int(re.search(r'%s(\d+)/' % url_delete, text).group(1))
    print("task_result_id: %s" % task_result_id)
    # In baseview.py: assert 0 < self.node <= self.SCRAPYD_SERVERS_AMOUNT
    # Note that AssertionError would be raise directly in test, whereas internal_server_error() would return 500.html
    # instead when the app is actually running, getting '500 error node index error: 2, which should be between 1 and 1'
    req(app, client, view='tasks', kws=dict(node=1, task_id=task_id, task_result_id=task_result_id),
        ins=["node: 1,", "server: '%s'," % app.config['SCRAPYD_SERVERS'][0], "status_code: 200,", "status: 'ok',",
             "node: 2,", "status_code: -1,", "status: 'exception',", "node index error", ":total='2'"])

    req(app, client, view='tasks.xhr', kws=dict(node=1, action='delete', task_id=task_id))


def test_delete_task_or_task_result_on_the_fly(app, client):
    for kind in ['delete_task', 'delete_task_result']:
        check_data_ = dict(check_data)

        req(app, client, view='schedule.check', kws=dict(node=NODE), data=check_data_,
            jskws=dict(cmd="-d _version=%s" % cst.VERSION, filename=FILENAME))

        with app.test_request_context():
            text, __ = req(app, client, view='schedule.run', kws=dict(node=NODE), data=run_data,
                           location=url_for('tasks', node=NODE))
        m = re.search(cst.TASK_NEXT_RUN_TIME_PATTERN, unquote_plus(text))
        task_id = int(m.group(1))
        print("task_id: %s" % task_id)

        __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='dump', task_id=task_id))
        assert js['data']['selected_nodes'] == [1, 2]

        sleep(2)
        # the first execution has not finished yet
        __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list', task_id=task_id))
        assert len(js['ids']) == 1
        task_result_id = js['ids'][0]
        __, js = req(app, client, view='tasks.xhr',
                     kws=dict(node=NODE, action='list', task_id=task_id, task_result_id=task_result_id))
        assert len(js['ids']) == 1

        if kind == 'delete_task':
            req(app, client, view='tasks.xhr',
                kws=dict(node=NODE, action='delete', task_id=task_id))
        else:
            req(app, client, view='tasks.xhr',
                kws=dict(node=NODE, action='delete', task_id=task_id, task_result_id=task_result_id))

        __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list'))
        if kind == 'delete_task':
            assert task_id not in js['ids']
        else:
            assert task_id in js['ids']

        __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list', task_id=task_id))
        assert len(js['ids']) == 0
        __, js = req(app, client, view='tasks.xhr',
                     kws=dict(node=NODE, action='list', task_id=task_id, task_result_id=task_result_id))
        assert len(js['ids']) == 0

        sleep(28)
        req(app, client, view='tasks.xhr',
            kws=dict(node=NODE, action='delete', task_id=task_id, task_result_id=task_result_id))
        __, js = req(app, client, view='tasks.xhr', kws=dict(node=NODE, action='list', task_id=task_id))
        assert len(js['ids']) == 0
        __, js = req(app, client, view='tasks.xhr',
                     kws=dict(node=NODE, action='list', task_id=task_id, task_result_id=task_result_id))
        assert len(js['ids']) == 0

        req(app, client, view='tasks.xhr', kws=dict(node=1, action='delete', task_id=task_id))
