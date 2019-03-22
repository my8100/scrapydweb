# coding: utf-8
import time

from flask import url_for
from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING

from scrapydweb import __version__
from scrapydweb.vars import SCHEDULER_STATE_DICT
from tests.utils import req


metadata = {}


def test_get_metadata(app, client):
    jskeys = [
        'jobs_per_page',  # tested
        'jobs_style',  #
        'id',
        'last_check_update_timestamp',  #
        'logparser_pid',
        'main_pid',
        'pageview',  #
        'password',
        'poll_pid',
        'scheduler_state',  #
        'tasks_per_page',  #
        'url_scrapydweb',
        'url_jobs',  #
        'url_schedule_task',  #
        'url_delete_task_result',  #
        'username',
        'version',  #
    ]
    with app.test_request_context():
        jskws = dict(
            version=__version__,
            url_jobs=url_for('jobs', node=1),  # '/1/jobs/',
            url_schedule_task=url_for('schedule.task', node=1),  # '/1/schedule/task/'
            # '/1/tasks/xhr/delete/1/1/'
            url_delete_task_result=url_for('tasks.xhr', node=1, action='delete', task_id=1, task_result_id=1)
        )
    __, js = req(app, client, view='metadata', kws=dict(node=1), jskeys=jskeys, jskws=jskws)
    print(js)
    metadata['last_check_update_timestamp'] = js['last_check_update_timestamp']


def test_last_check_update_timestamp(app, client):
    __, js = req(app, client, view='metadata', kws=dict(node=1),
                 jskws=dict(last_check_update_timestamp=metadata['last_check_update_timestamp'], pageview=1))
    assert time.time() - js['last_check_update_timestamp'] <= 3600 * 24 * 30


# :page-size="10"   size: '—',    long dash?!
def test_set_per_page(app, client):
    d = {10: u'—', 100: 'mini', 1000: 'mini'}
    for view in ['jobs', 'tasks']:
        for page in [10, 100, 1000, 100, 10]:
            __, js = req(app, client, view='metadata', kws=dict(node=1))
            another_per_page = 'tasks_per_page' if view == 'jobs' else 'jobs_per_page'
            before = js[another_per_page]

            ins = [":page-size='%s'" % page, "size: '%s'," % d[page]]
            req(app, client, view=view, kws=dict(node=1, style='database', per_page=page), ins=ins)
            req(app, client, view=view, kws=dict(node=1, style='database'), ins=ins)

            __, js = req(app, client, view='metadata', kws=dict(node=1))
            assert js['%s_per_page' % view] == page
            assert js[another_per_page] == before


def test_set_jobs_style(app, client):
    d = dict(database="Vue.extend(Main)", classic='class="table wrap"')
    for style in ['database', 'classic', 'database']:
        req(app, client, view='jobs', kws=dict(node=1, style=style), ins=d[style])
        req(app, client, view='metadata', kws=dict(node=1), jskws=dict(jobs_style=style))
        req(app, client, view='jobs', kws=dict(node=1, ui='mobile'), mobileui=True,
            ins='<table id="jobs", border="1">')
        req(app, client, view='jobs', kws=dict(node=1), ins=d[style])


def test_scheduler_state(app, client):
    for action, state in zip(['enable', 'disable', 'enable'], [STATE_RUNNING, STATE_PAUSED, STATE_RUNNING]):
        with app.test_request_context():
            if action == 'enable':
                scheduler_action_button = 'ENABLED'
                url_scheduler_action = url_for('tasks.xhr', node=1, action='disable')
            else:
                scheduler_action_button = 'DISABLED'
                url_scheduler_action = url_for('tasks.xhr', node=1, action='enable')
        req(app, client, view='tasks.xhr', kws=dict(node=1, action=action), ins=SCHEDULER_STATE_DICT[state])
        req(app, client, view='metadata', kws=dict(node=1), jskws=dict(scheduler_state=state))
        # ENABLED | DISABLED buttons
        req(app, client, view='tasks', kws=dict(node=1), ins=[scheduler_action_button, url_scheduler_action])
