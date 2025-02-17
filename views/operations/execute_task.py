# coding: utf-8
import json
import logging
import re
import time
import traceback

from ...common import get_now_string, get_response_from_view, handle_metadata
from ...models import Task, TaskResult, TaskJobResult, db
from ...utils.scheduler import scheduler


apscheduler_logger = logging.getLogger('apscheduler')

REPLACE_URL_NODE_PATTERN = re.compile(r'^/(\d+)/')
EXTRACT_URL_SERVER_PATTERN = re.compile(r'//(.+?:\d+)')


class TaskExecutor(object):

    def __init__(self, task_id, task_name, url_scrapydweb, url_schedule_task, url_delete_task_result,
                 auth, selected_nodes):
        self.task_id = task_id
        self.task_name = task_name
        self.url_scrapydweb = url_scrapydweb
        self.url_schedule_task = url_schedule_task
        self.url_delete_task_result = url_delete_task_result
        self.auth = auth
        self.data = dict(
            task_id=task_id,
            jobid='task_%s_%s' % (task_id, get_now_string(allow_space=False))
        )
        self.selected_nodes = selected_nodes
        self.task_result_id = None  # Be set in get_task_result_id()
        self.pass_count = 0
        self.fail_count = 0

        self.sleep_seconds_before_retry = 3
        self.nodes_to_retry = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def main(self):
        self.get_task_result_id()
        for index, nodes in enumerate([self.selected_nodes, self.nodes_to_retry]):
            if not nodes:
                continue
            if index == 1:
                # https://apscheduler.readthedocs.io/en/latest/userguide.html#shutting-down-the-scheduler
                self.logger.warning("Retry task #%s (%s) on nodes %s in %s seconds",
                                    self.task_id, self.task_name, nodes, self.sleep_seconds_before_retry)
                time.sleep(self.sleep_seconds_before_retry)
                self.logger.warning("Retrying task #%s (%s) on nodes %s", self.task_id, self.task_name, nodes)
            for node in nodes:
                result = self.schedule_task(node)
                if result:
                    if result['status'] == 'ok':
                        self.pass_count += 1
                    else:
                        self.fail_count += 1
                    self.db_insert_task_job_result(result)
        self.db_update_task_result()

    def get_task_result_id(self):
        # SQLite objects created in a thread can only be used in that same thread
        with db.app.app_context():
            task_result = TaskResult()
            task_result.task_id = self.task_id
            db.session.add(task_result)
            # db.session.flush()  # Get task_result.id before committing, flush() is part of commit()
            db.session.commit()
            # If directly use task_result.id later: Instance <TaskResult at 0x123> is not bound to a Session
            self.task_result_id = task_result.id
            self.logger.debug("Get new task_result_id %s for task #%s", self.task_result_id, self.task_id)

    def schedule_task(self, node):
        # TODO: Application was not able to create a URL adapter for request independent URL generation.
        # You might be able to fix this by setting the SERVER_NAME config variable.
        # with app.app_context():
        #     url_schedule_task = url_for('schedule.task', node=node)
        # http://127.0.0.1:5000/1/schedule/task/
        # /1/schedule/task/
        url_schedule_task = re.sub(REPLACE_URL_NODE_PATTERN, r'/%s/' % node, self.url_schedule_task)
        js = {}
        try:
            # assert '/1/' not in url_schedule_task, u"'故意出错'\r\n\"出错\"'故意出错'\r\n\"出错\""
            # assert False
            # time.sleep(10)
            js = get_response_from_view(url_schedule_task, auth=self.auth, data=self.data, as_json=True)
            assert js['status_code'] == 200 and js['status'] == 'ok', "Request got %s" % js
        except Exception as err:
            if node not in self.nodes_to_retry:
                apscheduler_logger.warning("Fail to execute task #%s (%s) on node %s, would retry later: %s",
                                           self.task_id, self.task_name, node, err)
                self.nodes_to_retry.append(node)
                return {}
            else:
                apscheduler_logger.error("Fail to execute task #%s (%s) on node %s, no more retries: %s",
                                         self.task_id, self.task_name, node, traceback.format_exc())
                js.setdefault('url', self.url_scrapydweb)  # '127.0.0.1:5000'
                js.setdefault('status_code', -1)
                js.setdefault('status', 'exception')
                js.setdefault('exception', traceback.format_exc())
        js.update(node=node)
        return js

    def db_insert_task_job_result(self, js):
        with db.app.app_context():
            if not TaskResult.query.get(self.task_result_id):
                apscheduler_logger.error("task_result #%s of task #%s not found", self.task_result_id, self.task_id)
                apscheduler_logger.warning("Discard task_job_result of task_result #%s of task #%s: %s",
                                           self.task_result_id, self.task_id, js)
                return
            task_job_result = TaskJobResult()
            task_job_result.task_result_id = self.task_result_id
            task_job_result.node = js['node']
            task_job_result.server = re.search(EXTRACT_URL_SERVER_PATTERN, js['url']).group(1)  # '127.0.0.1:6800'
            task_job_result.status_code = js['status_code']
            task_job_result.status = js['status']
            task_job_result.result = js.get('jobid', '') or js.get('message', '') or js.get('exception', '')
            db.session.add(task_job_result)
            db.session.commit()
            self.logger.info("Inserted task_job_result: %s", task_job_result)

    # https://stackoverflow.com/questions/13895176/sqlalchemy-and-sqlite-database-is-locked
    def db_update_task_result(self):
        with db.app.app_context():
            task = Task.query.get(self.task_id)
            task_result = TaskResult.query.get(self.task_result_id)
            if not task:
                apscheduler_logger.error("Task #%s not found", self.task_id)
                # if task_result:
                # '/1/tasks/xhr/delete/1/1/'
                url_delete_task_result = re.sub(r'/\d+/\d+/$', '/%s/%s/' % (self.task_id, self.task_result_id),
                                                self.url_delete_task_result)
                js = get_response_from_view(url_delete_task_result, auth=self.auth, data=self.data, as_json=True)
                apscheduler_logger.warning("Deleted task_result #%s [FAIL %s, PASS %s] of task #%s: %s",
                                           self.task_result_id, self.fail_count, self.pass_count, self.task_id, js)
                return
            if not task_result:
                apscheduler_logger.error("task_result #%s of task #%s not found", self.task_result_id, self.task_id)
                apscheduler_logger.warning("Failed to update task_result #%s [FAIL %s, PASS %s] of task #%s",
                                           self.task_result_id, self.fail_count, self.pass_count, self.task_id)
                return
            task_result.fail_count = self.fail_count
            task_result.pass_count = self.pass_count
            db.session.commit()
            self.logger.info("Inserted task_result: %s", task_result)


def execute_task(task_id):
    with db.app.app_context():
        task = Task.query.get(task_id)
        apscheduler_job = scheduler.get_job(str(task_id))
        if not task:
            apscheduler_job.remove()
            apscheduler_logger.error("apscheduler_job #{id} removed since task #{id} not exist. ".format(id=task_id))
        else:
            metadata = handle_metadata()
            username = metadata.get('username', '')
            password = metadata.get('password', '')
            url_delete_task_result = metadata.get('url_delete_task_result', '/1/tasks/xhr/delete/1/1/')
            task_executor = TaskExecutor(task_id=task_id,
                                         task_name=task.name,
                                         url_scrapydweb=metadata.get('url_scrapydweb', 'http://127.0.0.1:5000'),
                                         url_schedule_task=metadata.get('url_schedule_task', '/1/schedule/task/'),
                                         url_delete_task_result=url_delete_task_result,
                                         auth=(username, password) if username and password else None,
                                         selected_nodes=json.loads(task.selected_nodes))
            try:
                task_executor.main()
            except Exception:
                apscheduler_logger.error(traceback.format_exc())
