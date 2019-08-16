# coding: utf-8
from collections import OrderedDict
from datetime import datetime
import io
import json
import logging
from math import ceil
import os
import pickle
import re
import traceback

from flask import Blueprint, redirect, render_template, request, send_file, url_for

from ...models import Task, db
from ...vars import RUN_SPIDER_HISTORY_LOG, UA_DICT
from ..baseview import BaseView
from .execute_task import execute_task
from .utils import slot


apscheduler_logger = logging.getLogger('apscheduler')


def generate_cmd(auth, url, data):
    if auth:
        cmd = 'curl -u %s:%s %s' % (auth[0], auth[1], url)
    else:
        cmd = 'curl %s' % url

    for key, value in data.items():
        if key == 'setting':
            for v in value:
                t = (tuple(v.split('=', 1)))
                if v.startswith('USER_AGENT='):
                    cmd += ' --data-urlencode "setting=%s=%s"' % t
                else:
                    cmd += ' -d setting=%s=%s' % t
        elif key != '__task_data':
            cmd += ' -d %s=%s' % (key, value)

    return cmd


bp = Blueprint('schedule', __name__, url_prefix='/')


@bp.route('/schedule/history/')
def history():
    return send_file(RUN_SPIDER_HISTORY_LOG, mimetype='text/plain', cache_timeout=0)


class ScheduleView(BaseView):

    def __init__(self):
        super(ScheduleView, self).__init__()

        self.project = self.view_args['project']
        self.version = self.view_args['version']
        self.spider = self.view_args['spider']
        self.task_id = request.args.get('task_id', default=None, type=int)
        self.task = None

        self.url = 'http://%s/schedule.json' % self.SCRAPYD_SERVER
        self.template = 'scrapydweb/schedule.html'
        self.kwargs = {}

        self.selected_nodes = []
        self.first_selected_node = None

    def dispatch_request(self, **kwargs):
        if self.task_id:
            self.task = Task.query.get(self.task_id)
            if not self.task:
                message = "Task #%s not found" % self.task_id
                self.logger.error(message)
                return render_template(self.template_fail, node=self.node, message=message)
            self.query_task()
        elif self.POST:
            self.selected_nodes = self.get_selected_nodes()
            self.first_selected_node = self.selected_nodes[0]
        else:
            if self.project:
                # START button of Jobs page / Run Spider button of Logs page
                self.selected_nodes = [self.node]
            else:
                self.selected_nodes = []
            self.first_selected_node = self.node

        self.update_kwargs()
        return render_template(self.template, **self.kwargs)

    def query_task(self):
        task = self.task
        self.project = task.project
        self.version = task.version
        self.spider = task.spider

        self.selected_nodes = json.loads(task.selected_nodes)
        self.first_selected_node = self.selected_nodes[0]

        # 'settings_arguments': {'arg1': '233', 'setting': ['CLOSESPIDER_PAGECOUNT=10',]}
        settings_arguments = json.loads(task.settings_arguments)
        self.kwargs['expand_settings_arguments'] = len(settings_arguments) > 1 or settings_arguments['setting']
        settings_dict = dict(s.split('=') for s in settings_arguments.pop('setting'))
        arguments_dict = settings_arguments

        self.kwargs['jobid'] = task.jobid or self.get_now_string()
        USER_AGENT = settings_dict.pop('USER_AGENT', '')
        # Chrome|iPhone|iPad|Android
        self.kwargs['USER_AGENT'] = dict((v, k) for k, v in UA_DICT.items()).get(USER_AGENT, '')
        for k in ['ROBOTSTXT_OBEY', 'COOKIES_ENABLED']:
            v = settings_dict.pop(k, '')
            self.kwargs[k] = v if v in ['True', 'False'] else ''
        self.kwargs['CONCURRENT_REQUESTS'] = settings_dict.pop('CONCURRENT_REQUESTS', '')
        self.kwargs['DOWNLOAD_DELAY'] = settings_dict.pop('DOWNLOAD_DELAY', '')
        # "-d setting=CLOSESPIDER_TIMEOUT=60\r\n-d setting=CLOSESPIDER_PAGECOUNT=10\r\n-d arg1=val1"
        additional = ''
        # Use sorted() for Python 2
        for k, v in sorted(settings_dict.items()):
            additional += "-d setting=%s=%s\r\n" % (k, v)
        for k, v in sorted(arguments_dict.items()):
            additional += "-d %s=%s\r\n" % (k, v)
        # print(repr(additional))
        self.kwargs['additional'] = additional

        self.kwargs['expand_timer_task'] = True
        self.kwargs['task_id'] = self.task_id
        self.kwargs['name'] = task.name or 'task #%s' % self.task_id
        if not self.kwargs['name'].endswith(' - edit'):
            self.kwargs['name'] += ' - edit'

        self.kwargs['year'] = task.year or '*'
        self.kwargs['month'] = task.month or '*'
        self.kwargs['day'] = task.day or '*'
        self.kwargs['week'] = task.week or '*'
        # To avoid SyntaxError in javascript with Python 2: day_of_week: [u'*'],
        self.kwargs['day_of_week'] = [str(s.strip()) for s in task.day_of_week.split(',')] or ['*']  # 'mon-fri,sun'
        self.kwargs['hour'] = task.hour or '*'
        self.kwargs['minute'] = task.minute or '0'
        self.kwargs['second'] = task.second or '0'

        self.kwargs['start_date'] = task.start_date or ''
        self.kwargs['end_date'] = task.end_date or ''

        if task.timezone:  # To avoid showing 'None' when editing the task
            self.kwargs['timezone'] = task.timezone
        self.kwargs['jitter'] = max(0, task.jitter)
        self.kwargs['misfire_grace_time'] = max(0, task.misfire_grace_time)
        self.kwargs['coalesce'] = task.coalesce if task.coalesce in ['True', 'False'] else 'True'
        self.kwargs['max_instances'] = max(1, task.max_instances)

    def update_kwargs(self):
        self.kwargs.update(dict(
            node=self.node,
            url=self.url,
            url_deploy=url_for('deploy', node=self.node),
            project=self.project,
            version=self.version,
            spider=self.spider,
            # jobid=self.get_now_string(),
            selected_nodes=self.selected_nodes,
            first_selected_node=self.first_selected_node,
            url_servers=url_for('servers', node=self.node, opt='schedule'),
            url_schedule_run=url_for('schedule.run', node=self.node),
            url_schedule_history=url_for('schedule.history'),
            url_listprojects=url_for('api', node=self.node, opt='listprojects'),
            url_listversions=url_for('api', node=self.node, opt='listversions', project='PROJECT_PLACEHOLDER'),
            url_listspiders=url_for('api', node=self.node, opt='listspiders', project='PROJECT_PLACEHOLDER',
                                    version_spider_job='VERSION_PLACEHOLDER'),
            url_schedule_check=url_for('schedule.check', node=self.node)
        ))
        self.kwargs.setdefault('expand_settings_arguments', self.SCHEDULE_EXPAND_SETTINGS_ARGUMENTS)
        self.kwargs.setdefault('jobid', '')
        # self.kwargs.setdefault('UA_DICT', UA_DICT)
        self.kwargs.setdefault('CUSTOM_USER_AGENT', self.SCHEDULE_CUSTOM_USER_AGENT)
        # custom|Chrome|iPhone|iPad|Android
        self.kwargs.setdefault('USER_AGENT', '' if self.SCHEDULE_USER_AGENT is None else self.SCHEDULE_USER_AGENT)
        self.kwargs.setdefault('ROBOTSTXT_OBEY', '' if self.SCHEDULE_ROBOTSTXT_OBEY is None else self.SCHEDULE_ROBOTSTXT_OBEY)
        self.kwargs.setdefault('COOKIES_ENABLED', '' if self.SCHEDULE_COOKIES_ENABLED is None else self.SCHEDULE_COOKIES_ENABLED)
        self.kwargs.setdefault('CONCURRENT_REQUESTS', '' if self.SCHEDULE_CONCURRENT_REQUESTS is None else self.SCHEDULE_CONCURRENT_REQUESTS)
        self.kwargs.setdefault('DOWNLOAD_DELAY', '' if self.SCHEDULE_DOWNLOAD_DELAY is None else self.SCHEDULE_DOWNLOAD_DELAY)
        # additional = "-d setting=CLOSESPIDER_TIMEOUT=60\r\n-d setting=CLOSESPIDER_PAGECOUNT=10\r\n-d arg1=val1"
        self.kwargs.setdefault('additional', self.SCHEDULE_ADDITIONAL)

        self.kwargs.setdefault('expand_timer_task', 'add_task' in request.args)  # '+' button in the TimeTasks page
        self.kwargs.setdefault('task_id', 0)
        self.kwargs['action'] = 'add_fire'
        self.kwargs['trigger'] = 'cron'
        self.kwargs.setdefault('name', '')
        self.kwargs['replace_existing'] = 'True'

        self.kwargs.setdefault('year', '*')
        self.kwargs.setdefault('month', '*')
        self.kwargs.setdefault('day', '*')
        self.kwargs.setdefault('week', '*')
        self.kwargs.setdefault('day_of_week', ['*'])  # 'mon-fri, sun'
        self.kwargs.setdefault('hour', '*')
        self.kwargs.setdefault('minute', '0')
        self.kwargs.setdefault('second', '0')

        self.kwargs.setdefault('start_date', '')
        self.kwargs.setdefault('end_date', '')

        self.kwargs.setdefault('timezone', self.scheduler.timezone)
        self.kwargs.setdefault('jitter', 0)
        self.kwargs.setdefault('misfire_grace_time', 600)
        self.kwargs.setdefault('coalesce', 'True')
        self.kwargs.setdefault('max_instances', 1)


class ScheduleCheckView(BaseView):

    def __init__(self):
        super(ScheduleCheckView, self).__init__()

        self.url = 'http://%s/schedule.json' % self.SCRAPYD_SERVER
        self.template = 'scrapydweb/schedule.html'

        self.filename = ''
        self.data = OrderedDict()
        self.slot = slot

    def dispatch_request(self, **kwargs):
        self.logger.debug('request.form from %s\n%s', request.url, self.json_dumps(request.form))
        self.prepare_data()
        self.update_data_for_timer_task()
        # self.logger.warning(self.json_dumps(self.data))  # TypeError: Object of type datetime is not JSON serializable
        cmd = generate_cmd(self.AUTH, self.url, self.data)
        # '-d' may be in project name, like 'ScrapydWeb-demo'
        cmd = re.sub(r'(curl -u\s+.*?:.*?)\s+(http://)', r'\1 \\\r\n\2', cmd)
        cmd = re.sub(r'\s+-d\s+', ' \\\r\n-d ', cmd)
        cmd = re.sub(r'\s+--data-urlencode\s+', ' \\\r\n--data-urlencode ', cmd)
        return self.json_dumps({'filename': self.filename, 'cmd': cmd}, as_response=True)

    def prepare_data(self):
        for k, d in [('project', 'projectname'), ('_version', self.DEFAULT_LATEST_VERSION),
                     ('spider', 'spidername')]:
            self.data[k] = request.form.get(k, d)
        if self.data['_version'] == self.DEFAULT_LATEST_VERSION:
            self.data.pop('_version')

        jobid = request.form.get('jobid') or self.get_now_string()
        self.data['jobid'] = re.sub(self.LEGAL_NAME_PATTERN, '-', jobid)

        self.data['setting'] = []
        ua = UA_DICT.get(request.form.get('USER_AGENT', ''), '')
        if ua:
            self.data['setting'].append('USER_AGENT=%s' % ua)

        for key in ['ROBOTSTXT_OBEY', 'COOKIES_ENABLED', 'CONCURRENT_REQUESTS', 'DOWNLOAD_DELAY']:
            value = request.form.get(key, '')
            if value:
                self.data['setting'].append("%s=%s" % (key, value))

        additional = request.form.get('additional', '').strip()
        if additional:
            parts = [i.strip() for i in re.split(r'-d\s+', re.sub(r'[\r\n]', ' ', additional)) if i.strip()]
            for part in parts:
                part = re.sub(r'\s*=\s*', '=', part)
                if '=' not in part:
                    continue
                m_setting = re.match(r'setting=([A-Z_]{6,31}=.+)', part)  # 'EDITOR' 'DOWNLOADER_CLIENTCONTEXTFACTORY'
                if m_setting:
                    self.data['setting'].append(m_setting.group(1))
                    continue
                m_arg = re.match(r'([a-zA-Z_][0-9a-zA-Z_]*)=(.+)', part)
                if m_arg and m_arg.group(1) != 'setting':
                    self.data[m_arg.group(1)] = m_arg.group(2)

        self.data['setting'].sort()
        _version = self.data.get('_version', 'default-the-latest-version')
        _filename = '{project}_{version}_{spider}'.format(project=self.data['project'],
                                                          version=_version,
                                                          spider=self.data['spider'])
        self.filename = '%s.pickle' % re.sub(self.LEGAL_NAME_PATTERN, '-', _filename)
        filepath = os.path.join(self.SCHEDULE_PATH, self.filename)
        with io.open(filepath, 'wb') as f:
            f.write(pickle.dumps(self.data))

        self.slot.add_data(self.filename, self.data)

    def get_int_from_form(self, key, default, minimum):
        value = request.form.get(key) or default
        try:
            return max(minimum, int(ceil(float(value))))
        except (TypeError, ValueError) as err:
            self.logger.warning("%s. The value of request.form['%s'] would be set as %s", err, key, default)
            return default

    def update_data_for_timer_task(self):
        if not request.form.get('trigger'):
            return
        # In case passing '-d task_data=xxx' in the additional text box
        self.data['__task_data'] = dict(
            action=request.form.get('action') or 'add_fire',
            task_id=request.form.get('task_id', default=0, type=int),

            # trigger=request.form.get('trigger') or 'cron',
            trigger='cron',
            # id =  # put off in ScheduleRunView.db_insert_task()
            name=request.form.get('name') or None,  # (str) – the description of this job   None
            replace_existing=request.form.get('replace_existing', 'True') == 'True',

            year=request.form.get('year') or '*',  # (int|str) – 4-digit year
            month=request.form.get('month') or '*',  # (int|str) – month (1-12)
            day=request.form.get('day') or '*',  # (int|str) – day of the (1-31)
            week=request.form.get('week') or '*',  # (int|str) – ISO week (1-53)
            # (int|str) – number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)
            day_of_week=request.form.get('day_of_week') or '*',  # From browser: "*"|"*,mon-fri"|"", May be '0',
            hour=request.form.get('hour') or '*',  # (int|str) – hour (0-23) May be '0'
            minute=request.form.get('minute') or '0',  # (int|str) – minute (0-59)    0
            second=request.form.get('second') or '0',  # (int|str) – second (0-59)    0

            start_date=request.form.get('start_date') or None,  # (datetime|str)    None
            end_date=request.form.get('end_date') or None,  # (datetime|str)        None
            # from tzlocal import get_localzone
            # <DstTzInfo 'Asia/Shanghai' LMT+8:06:00 STD>   +8
            # <DstTzInfo 'US/Eastern' LMT-1 day, 19:04:00 STD>  -5
            timezone=request.form.get('timezone') or None,  # (datetime.tzinfo|str)     defaults to scheduler timezone
            jitter=self.get_int_from_form('jitter', 0, minimum=0),  # (int|None)
            # TypeError: misfire_grace_time must be either None or a positive integer
            # Passing '0' would be saved as None for positive infinity.
            misfire_grace_time=self.get_int_from_form('misfire_grace_time', 600, minimum=0) or None,  # (int)
            coalesce=(request.form.get('coalesce') or 'True') == 'True',  # (bool)
            # TypeError: max_instances must be a positive integer
            max_instances=self.get_int_from_form('max_instances', 1, minimum=1)  # (int)
        )


class ScheduleRunView(BaseView):

    def __init__(self):
        super(ScheduleRunView, self).__init__()

        self.url = ''
        self.template = 'scrapydweb/schedule_results.html'

        self.slot = slot
        self.selected_nodes_amount = 0
        self.selected_nodes = []
        self.first_selected_node = 0
        self.filename = request.form['filename']
        self.data = {}
        self.task_data = {}
        self.task = None
        self.task_id = 0
        self._action = ''
        self.to_update_task = False
        self.add_task_result = False
        self.add_task_flash = ''
        self.add_task_error = ''
        self.add_task_message = ''
        self.js = {}

    def dispatch_request(self, **kwargs):
        self.handle_form()
        self.handle_action()
        self.update_history()
        return self.generate_response()

    def handle_form(self):
        self.selected_nodes_amount = request.form.get('checked_amount', default=0, type=int)
        # With multinodes, would try to Schedule to the first selected node first
        if self.selected_nodes_amount:
            self.selected_nodes = self.get_selected_nodes()
            self.first_selected_node = self.selected_nodes[0]
            self.url = 'http://%s/schedule.json' % self.SCRAPYD_SERVERS[self.first_selected_node - 1]
            # Note that self.first_selected_node != self.node
            self.AUTH = self.SCRAPYD_SERVERS_AUTHS[self.first_selected_node - 1]
        else:
            self.selected_nodes = [self.node]
            self.url = 'http://%s/schedule.json' % self.SCRAPYD_SERVER

        # in handle_action():   self.data.pop('__task_data', {})    self.task_data.pop
        self.data = self.slot.data.get(self.filename, {})
        # self.data = None  # For test only
        if not self.data:
            filepath = os.path.join(self.SCHEDULE_PATH, self.filename)
            with io.open(filepath, 'rb') as f:
                self.data = pickle.loads(f.read())

    def handle_action(self):
        self.logger.debug(self.json_dumps(self.data))
        self.task_data = self.data.pop('__task_data', {})  # Now self.data is clean
        self.logger.debug("task_data: %s", self.task_data)
        if self.task_data:  # For timer task
            self._action = self.task_data.pop('action')  # add|add_fire|add_pause
            self.task_id = self.task_data.pop('task_id')  # 0|positive int from edit button in the Timer Tasks page
            self.to_update_task = self.task_data.pop('replace_existing') and self.task_id  # replace_existing: bool
            self.db_insert_update_task()
            self.add_update_task()
        else:
            self._action = 'run'
            status_code, self.js = self.make_request(self.url, data=self.data, auth=self.AUTH)

    # https://apscheduler.readthedocs.io/en/latest/userguide.html
    # https://apscheduler.readthedocs.io/en/latest/modules/triggers/cron.html#module-apscheduler.triggers.cron
    def db_insert_update_task(self):
        if self.to_update_task:
            self.task = Task.query.get(self.task_id)
            self.logger.debug("Selected %s", self.task)
            self.db_process_task()
            self.task.update_time = datetime.now()
            # Put off in add_update_task()
            # db.session.commit()
            # self.logger.debug("Updated %s", self.task)
        else:
            self.task = Task()
            self.db_process_task()
            db.session.add(self.task)
            db.session.commit()
            self.logger.debug("Inserted %s", self.task)
            self.task_id = self.task.id

    def db_process_task(self):
        data = dict(self.data)  # Used in update_history() and generate_response()

        self.task.project = data.pop('project')
        self.task.version = data.pop('_version', self.DEFAULT_LATEST_VERSION)
        self.task.spider = data.pop('spider')
        self.task.jobid = data.pop('jobid')
        self.task.settings_arguments = self.json_dumps(data, sort_keys=True, indent=None)
        self.task.selected_nodes = str(self.selected_nodes)

        self.task.name = self.task_data['name']
        self.task.trigger = self.task_data['trigger']

        self.task.year = self.task_data['year']
        self.task.month = self.task_data['month']
        self.task.day = self.task_data['day']
        self.task.week = self.task_data['week']
        self.task.day_of_week = self.task_data['day_of_week']
        self.task.hour = self.task_data['hour']
        self.task.minute = self.task_data['minute']
        self.task.second = self.task_data['second']
        self.task.start_date = self.task_data['start_date']
        self.task.end_date = self.task_data['end_date']

        self.task.timezone = self.task_data['timezone']
        self.task.jitter = self.task_data['jitter']
        self.task.misfire_grace_time = self.task_data['misfire_grace_time']
        self.task.coalesce = 'True' if self.task_data['coalesce'] else 'False'  # bool True would be stored as 1
        self.task.max_instances = self.task_data['max_instances']

    # https://apscheduler.readthedocs.io/en/latest/modules/schedulers/base.html#apscheduler.schedulers.base.BaseScheduler.add_job
    def add_update_task(self):
        # class apscheduler.schedulers.base.BaseScheduler
        # def add_job(self, func, trigger=None, args=None, kwargs=None, id=None, name=None,
        #             misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
        #             next_run_time=undefined, jobstore='default', executor='default',
        #             replace_existing=False, **trigger_args):
        # TODO: hard coding of url_schedule_task
        # if 'url_schedule_task' not in self.metadata:
        #     url_schedule_task = url_for('schedule.task', node=1)  # /1/schedule/task/
        #     handle_metadata('url_schedule_task', url_schedule_task)
        kwargs = dict(task_id=self.task_id)
        self.task_data['id'] = str(self.task_id)  # TypeError: id must be a nonempty string
        # apscheduler.executors.default: Job "execute_task (trigger: cron[year='*'..." executed successfully
        self.task_data['name'] = self.task_data['name'] or 'task_%s' % self.task_id  # To replace execute_task with name

        # next_run_time (datetime) – when to first run the job, regardless of the trigger
        # (pass None to add the job as paused)
        if self._action == 'add_fire':
            # In case the task fires before db.session.commit()
            if self.to_update_task:
                self.logger.info("Task #%s would be fired right after the apscheduler_job is updated", self.task_id)
            else:
                self.task_data['next_run_time'] = datetime.now()  # datetime.utcnow()
            postfix = "Reload this page several seconds later to check out the execution result. "
        elif self._action == 'add_pause':
            self.task_data['next_run_time'] = None
            postfix = "Click the Paused button to resume it. "
        else:
            postfix = "Click the Running button to pause it. "

        # https://apscheduler.readthedocs.io/en/latest/modules/schedulers/base.html#apscheduler.schedulers.base.BaseScheduler.add_job
        msg = ''
        try:
            # assert False, u"'故意出错'\r\n\"出错\""
            job_instance = self.scheduler.add_job(func=execute_task, args=None, kwargs=kwargs,
                                                  replace_existing=True, **self.task_data)
        except Exception as err:
            # ValueError: Unrecognized expression "10/*" for field "second"
            if self.to_update_task:
                db.session.rollback()
                self.logger.warning("Rollback %s", self.task)
            self.add_task_result = False
            self.add_task_error = str(err)
            msg = traceback.format_exc()
            self.logger.error(msg)
        else:
            # https://apscheduler.readthedocs.io/en/latest/modules/triggers/cron.html#daylight-saving-time-behavior
            # either use a timezone that does not observe DST, for instance UTC
            # https://www.douban.com/note/147740972/
            # F12 Date() Tue Jan 29 2019 13:30:57 GMT+0800 (China Standard Time)
            # https://www.timeanddate.com/time/zones/cst
            # Other time zones named CST: China Standard Time, Cuba Standard Time
            if self.to_update_task:
                db.session.commit()
                self.logger.debug("Updated %s", self.task)
                # In case the task fires before db.session.commit()
                if self._action == 'add_fire':
                    self.logger.info("Modifying next_run_time of updated task #%s to fire it right now", self.task_id)
                    job_instance.modify(next_run_time=datetime.now())
            self.add_task_result = True
            msg = u"{target} task #{task_id} ({task_name}) successfully, next run at {next_run_time}. ".format(
                target="Update" if self.to_update_task else 'Add',
                task_id=self.task_id, task_name=self.task_data['name'],
                next_run_time=job_instance.next_run_time or self.NA)
            self.add_task_flash = msg + postfix
            apscheduler_logger.warning(msg)
            # TypeError: vars() argument must have __dict__ attribute
            # apscheduler_logger.warning(vars(job_instance))
            # pformat({k: getattr(job_instance, k) for k in job_instance.__slots__}, indent=4)
            job_instance_dict = dict(
                id=job_instance.id,
                name=job_instance.name,
                kwargs=job_instance.kwargs,
                misfire_grace_time=job_instance.misfire_grace_time,
                max_instances=job_instance.max_instances,
                trigger=repr(job_instance.trigger),
                next_run_time=repr(job_instance.next_run_time),
            )
            apscheduler_logger.warning("%s job_instance: \n%s", "Updated" if self.to_update_task else 'Added',
                                       self.json_dumps(job_instance_dict))
        finally:
            if 'next_run_time' in self.task_data:  # TypeError: Object of type datetime is not JSON serializable
                self.task_data['next_run_time'] = str(self.task_data['next_run_time'] or self.NA)
            self.add_task_message = (u"{msg}\nkwargs for execute_task():\n{kwargs}\n\n"
                                     u"task_data for scheduler.add_job():\n{task_data}").format(
                msg=msg, kwargs=self.json_dumps(kwargs), task_data=self.json_dumps(self.task_data))
            self.logger.debug(self.add_task_message)

    def update_history(self):
        with io.open(RUN_SPIDER_HISTORY_LOG, 'r+', encoding='utf-8') as f:
            content_backup = f.read()
            f.seek(0)
            content = os.linesep.join([
                '%s %s <%s>' % ('#' * 50, self.get_now_string(True), self._action),
                str([self.SCRAPYD_SERVERS[i - 1] for i in self.selected_nodes]),
                generate_cmd(self.AUTH, self.url, self.data),
                self.add_task_message or self.json_dumps(self.js),
                ''
            ])
            f.write(content)
            f.write(content_backup)

    def generate_response(self):
        if self._action in ['add', 'add_fire', 'add_pause']:
            if self.add_task_result:
                return redirect(url_for('tasks', node=self.node, flash=self.add_task_flash))
            else:
                return render_template(self.template_fail, node=self.node,
                                       alert="Fail to add/edit task with error:",
                                       text=self.add_task_error,
                                       tip=("Check out the HELP section in the Run Spider page, and then "
                                            "go back to the Timer Tasks page to re-edit task #%s. ") % self.task_id,
                                       message=self.add_task_message)
        if self.js['status'] == self.OK:
            if not self.selected_nodes_amount:
                return redirect(url_for('jobs', node=self.node))

            kwargs = dict(
                node=self.node,
                project=self.data['project'],
                version=self.data.get('_version', self.DEFAULT_LATEST_VERSION),
                spider=self.data['spider'],
                selected_nodes=self.selected_nodes,
                first_selected_node=self.first_selected_node,
                js=self.js,
                url_stats_list=[url_for('log', node=node, opt='stats', project=self.data['project'],
                                        spider=self.data['spider'], job=self.data['jobid'])
                                for node in range(1, self.SCRAPYD_SERVERS_AMOUNT + 1)],
                url_xhr=url_for('schedule.xhr', node=self.node, filename=self.filename),
                url_servers=url_for('servers', node=self.node, opt='getreports', project=self.data['project'],
                                    spider=self.data['spider'], version_job=self.data['jobid'])
            )
            return render_template(self.template, **kwargs)
        else:
            if self.selected_nodes_amount > 1:
                alert = ("Multinode schedule terminated, "
                         "since the first selected node returned status: " + self.js['status'])
            else:
                alert = "Fail to schedule, got status: " + self.js['status']

            message = self.js.get('message', '')
            if message:
                self.js['message'] = 'See details below'

            return render_template(self.template_fail, node=self.node,
                                   alert=alert, text=self.json_dumps(self.js), message=message)


class ScheduleXhrView(BaseView):

    def __init__(self):
        super(ScheduleXhrView, self).__init__()

        self.filename = self.view_args['filename']
        self.url = 'http://%s/schedule.json' % self.SCRAPYD_SERVER
        self.slot = slot
        self.data = None

    def dispatch_request(self, **kwargs):
        self.data = self.slot.data.get(self.filename)
        # self.data = None  # For test only
        if not self.data:
            filepath = os.path.join(self.SCHEDULE_PATH, self.filename)
            with io.open(filepath, 'rb') as f:
                self.data = pickle.loads(f.read())

        status_code, js = self.make_request(self.url, data=self.data, auth=self.AUTH)
        return self.json_dumps(js, as_response=True)


class ScheduleTaskView(BaseView):

    def __init__(self):
        super(ScheduleTaskView, self).__init__()

        self.url = 'http://%s/schedule.json' % self.SCRAPYD_SERVER
        self.task_id = request.form['task_id']
        self.jobid = request.form['jobid']
        self.data = {}

    def dispatch_request(self, **kwargs):
        task = Task.query.get(self.task_id)
        if not task:
            message = "Task #%s not found" % self.task_id
            self.logger.error(message)
            js = dict(url=self.url, auth=self.AUTH, status_code=-1, status=self.ERROR, message=message)
        else:
            self.data['project'] = task.project
            if task.version != self.DEFAULT_LATEST_VERSION:
                self.data['_version'] = task.version
            self.data['spider'] = task.spider
            self.data['jobid'] = self.jobid
            self.data.update(json.loads(task.settings_arguments))
            status_code, js = self.make_request(self.url, data=self.data, auth=self.AUTH)

        return self.json_dumps(js, as_response=True)
