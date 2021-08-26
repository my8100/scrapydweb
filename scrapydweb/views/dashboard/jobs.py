# coding: utf-8
from collections import OrderedDict
from datetime import datetime
import re
import traceback

from flask import flash, get_flashed_messages, render_template, request, url_for
from six.moves.urllib.parse import urljoin

from ...common import handle_metadata
from ...models import create_jobs_table, db
from ...vars import STRICT_NAME_PATTERN, jobs_table_map
from ..baseview import BaseView


_metadata = handle_metadata()
metadata = dict(
    pageview=_metadata.get('pageview', 1),
    per_page=_metadata.get('jobs_per_page', 100),
    style=_metadata.get('jobs_style', 'database'),
    unique_key_strings={}
)

STATUS_PENDING = '0'
STATUS_RUNNING = '1'
STATUS_FINISHED = '2'
NOT_DELETED = '0'
DELETED = '1'
HREF_PATTERN = re.compile(r"""href=['"](.+?)['"]""")  # Temp support for Scrapyd v1.3.0 (not released)
JOB_PATTERN = re.compile(r"""
                            <tr>
                                <td>(?P<Project>.*?)</td>
                                <td>(?P<Spider>.*?)</td>
                                <td>(?P<Job>.*?)</td>
                                (?:<td>(?P<PID>.*?)</td>)?
                                (?:<td>(?P<Start>.*?)</td>)?
                                (?:<td>(?P<Runtime>.*?)</td>)?
                                (?:<td>(?P<Finish>.*?)</td>)?
                                (?:<td>(?P<Log>.*?)</td>)?
                                (?:<td>(?P<Items>.*?)</td>)?
                                [\w\W]*?  # Temp support for Scrapyd v1.3.0 (not released)
                            </tr>
                          """, re.X)
JOB_KEYS = ['project', 'spider', 'job', 'pid', 'start', 'runtime', 'finish', 'href_log', 'href_items']


class JobsView(BaseView):
    # methods = ['GET']
    metadata = metadata

    def __init__(self):
        super(JobsView, self).__init__()

        style = request.args.get('style')
        self.style = style if style in ['database', 'classic'] else self.metadata['style']
        if self.style != self.metadata['style']:
            self.metadata['style'] = self.style
            handle_metadata('jobs_style', self.style)
            self.logger.debug("Change style to %s", self.metadata['style'])

        self.per_page = request.args.get('per_page', default=self.metadata['per_page'], type=int)
        if self.per_page != self.metadata['per_page']:
            self.metadata['per_page'] = self.per_page
            handle_metadata('jobs_per_page', self.per_page)
            self.logger.debug("Change per_page to %s", self.metadata['per_page'])
        self.page = request.args.get('page', default=1, type=int)

        self.url = 'http://%s/jobs' % self.SCRAPYD_SERVER
        if self.SCRAPYD_SERVER_PUBLIC_URL:
            self.public_url = '%s/jobs' % self.SCRAPYD_SERVER_PUBLIC_URL
        else:
            self.public_url = ''
        self.text = ''
        self.kwargs = {}
        if self.USE_MOBILEUI:
            self.style = 'classic'
            self.template = 'scrapydweb/jobs_mobileui.html'
        elif self.style == 'classic':
            self.template = 'scrapydweb/jobs_classic.html'
        else:  # 'database'
            self.template = 'scrapydweb/jobs.html'

        self.listjobs = request.args.get('listjobs', None)

        self.liststats_datas = {}
        self.jobs_dict = {}

        self.jobs = []
        self.jobs_backup = []
        self.pending_jobs = []
        self.running_jobs = []
        self.finished_jobs = []
        self.jobs_pagination = None

        self.Job = None  # database class Job

    def dispatch_request(self, **kwargs):
        status_code, self.text = self.make_request(self.url, auth=self.AUTH, as_json=False)
        if status_code != 200 or not re.search(r'<body><h1>Jobs</h1>', self.text):
            kwargs = dict(
                node=self.node,
                url=self.url,
                status_code=status_code,
                text=self.text,
                tip="Click the above link to make sure your Scrapyd server is accessable. "
            )
            return render_template(self.template_fail, **kwargs)
        # Temp support for Scrapyd v1.3.0 (not released)
        self.text = re.sub(r'<thead>.*?</thead>', '', self.text, flags=re.S)
        self.jobs = [dict(zip(JOB_KEYS, job)) for job in re.findall(JOB_PATTERN, self.text)]
        self.jobs_backup = list(self.jobs)

        if self.listjobs:
            return self.json_dumps(self.jobs, as_response=True)

        if self.POST:  # To update self.liststats_datas
            self.get_liststats_datas()
        else:
            self.metadata['pageview'] += 1
            self.logger.debug('metadata: %s', self.metadata)
            self.set_flash()
        if self.style == 'database' or self.POST:
            self.handle_jobs_with_db()
        if self.POST:
            try:
                self.set_jobs_dict()
            except:
                raise
            finally:
                get_flashed_messages()
            return self.json_dumps(self.jobs_dict, as_response=True)
        if self.style != 'database':
            self.jobs = self.jobs_backup
            self.handle_jobs_without_db()
        self.set_kwargs()
        return render_template(self.template, **self.kwargs)

    def set_flash(self):
        if self.metadata['pageview'] > 2 and self.metadata['pageview'] % 100:
            return
        if not self.ENABLE_AUTH and self.SCRAPYD_SERVERS_AMOUNT == 1:
            flash("Set 'ENABLE_AUTH = True' to enable basic auth for web UI", self.INFO)
        if self.IS_LOCAL_SCRAPYD_SERVER:
            if not self.LOCAL_SCRAPYD_LOGS_DIR:
                flash(("Set up the LOCAL_SCRAPYD_LOGS_DIR option to speed up the loading of scrapy logfiles "
                      "for the LOCAL_SCRAPYD_SERVER %s" % self.SCRAPYD_SERVER), self.WARN)
            if not self.ENABLE_LOGPARSER:
                flash("Set 'ENABLE_LOGPARSER = True' to run LogParser as a subprocess at startup", self.WARN)
        if not self.ENABLE_MONITOR and self.SCRAPYD_SERVERS_AMOUNT == 1:
            flash("Set 'ENABLE_MONITOR = True' to enable the monitor feature", self.INFO)

# stats.json by LogParser
# {
#     "status_code": 200,
#     "status": "ok",
#     "datas": {
#         "demo": {
#             "test": {
#                 "2019-01-01T0_00_01": {
#                     "pages": 3,
#                     "items": 2,
    def get_liststats_datas(self):
        # NOTE: get_response_from_view() would update g.url_jobs_list, unexpected for mobileui
        # request.url: http://localhost/1/api/liststats/
        # TODO: test https
        url_liststats = url_for('api', node=self.node, opt='liststats')
        js = self.get_response_from_view(url_liststats, as_json=True)
        if js['status'] == self.OK:
            self.liststats_datas = js.pop('datas', {})
            self.logger.debug("Got datas with %s entries from liststats: %s", len(self.liststats_datas), js)
        else:
            self.logger.warning("Fail to get datas from liststats: (%s) %s %s",
                                js['status_code'], js['status'], js.get('tip', ''))

    def create_table(self):
        self.Job = jobs_table_map.get(self.node, None)
        if self.Job is not None:
            self.logger.debug("Got table: %s", self.Job.__tablename__)
        else:
            self.Job = create_jobs_table(re.sub(STRICT_NAME_PATTERN, '_', self.SCRAPYD_SERVER))
            # sqlite3.OperationalError: table "127_0_0_1_6800" already exists
            db.create_all(bind='jobs')
            self.metadata[self.node] = self.Job
            jobs_table_map[self.node] = self.Job
            self.logger.debug("Created table: %s", self.Job.__tablename__)

    def handle_jobs_with_db(self):
        try:
            if request.args.get('raise_exception') == 'True':  # For test only
                assert False, "raise_exception: True"
            self.handle_unique_constraint()
            self.create_table()
            self.db_insert_jobs()
            self.db_clean_pending_jobs()
            self.query_jobs()
        except Exception as err:
            self.logger.error("Fail to persist jobs in database: %s", traceback.format_exc())
            db.session.rollback()
            flash("Fail to persist jobs in database: %s" % err, self.WARN)
            # sqlalchemy.exc.InvalidRequestError: Table '127_0_0_1_6800' is already defined for this MetaData instance.
            # Specify 'extend_existing=True' to redefine options and columns on an existing Table object.
            if "is already defined for this MetaData instance" in str(err):
                flash("Please restart ScrapydWeb to work around this occasional bug!", self.WARN)
            if self.style == 'database' and not self.POST:
                self.style = 'classic'
                self.template = 'scrapydweb/jobs_classic.html'
                self.metadata['style'] = self.style
                handle_metadata('jobs_style', self.style)
                msg = "Change style to %s" % self.style
                self.logger.info(msg)
                # flash(msg, self.WARN)

    # Note that there may be jobs with the same combination of (project, spider, job) in the fetched Jobs
    def handle_unique_constraint(self):
        seen_jobs = OrderedDict()
        for job in self.jobs:  # (Pending, Running) ASC
            if job['finish']:
                break
            unique_key = (job['project'], job['spider'], job['job'])
            if unique_key in seen_jobs:  # ignore previous
                start = seen_jobs[unique_key]['start']
                finish = seen_jobs[unique_key]['finish']
                unique_key_string = '/'.join(list(unique_key) + [start, finish, str(self.node)])
                if start:
                    msg = "Ignore seen running job: %s, started at %s" % ('/'.join(unique_key), start)
                else:
                    msg = "Ignore seen pending job: %s" % ('/'.join(unique_key))
                self.logger.debug(msg)
                if unique_key_string not in self.metadata['unique_key_strings']:  # flash only once
                    self.metadata['unique_key_strings'][unique_key_string] = None
                    flash(msg, self.WARN if start else self.INFO)
                seen_jobs.pop(unique_key)
            seen_jobs[unique_key] = job
        for job in reversed(self.jobs):  # Finished DESC
            if not job['finish']:
                break
            unique_key = (job['project'], job['spider'], job['job'])
            if unique_key in seen_jobs:  # ignore current
                unique_key_string = '/'.join(list(unique_key) + [job['start'], job['finish'], str(self.node)])
                msg = "Ignore seen finished job: %s, started at %s" % ('/'.join(unique_key), job['start'])
                self.logger.debug(msg)
                if unique_key_string not in self.metadata['unique_key_strings']:
                    self.metadata['unique_key_strings'][unique_key_string] = None
                    flash(msg, self.INFO)
            else:
                seen_jobs[unique_key] = job
        self.jobs = list(seen_jobs.values())

    def db_insert_jobs(self):
        records = []
        for job in self.jobs:  # set(self.jobs): unhashable type: 'dict'
            record = self.Job.query.filter_by(project=job['project'], spider=job['spider'], job=job['job']).first()
            if record:
                self.logger.debug("Found job in database: %s", record)
                if record.deleted == DELETED:
                    if record.status == STATUS_FINISHED and str(record.start) == job['start']:
                        self.logger.info("Ignore deleted job: %s", record)
                        continue
                    else:
                        record.deleted = NOT_DELETED
                        record.pages = None
                        record.items = None
                        self.logger.info("Recover deleted job: %s", record)
                        flash("Recover deleted job: %s" % job, self.WARN)
            else:
                record = self.Job()
            records.append(record)
            for k, v in job.items():
                v = v or None  # Save NULL in database for empty string
                if k in ['start', 'finish']:
                    v = datetime.strptime(v, '%Y-%m-%d %H:%M:%S') if v else None  # Avoid empty string
                elif k in ['href_log', 'href_items']:  # <a href='/logs/demo/test/xxx.log'>Log</a>
                    m = re.search(HREF_PATTERN, v) if v else None
                    v = m.group(1) if m else v
                setattr(record, k, v)
            if not job['start']:
                record.status = STATUS_PENDING
            elif not job['finish']:
                record.status = STATUS_RUNNING
            else:
                record.status = STATUS_FINISHED
            if not job['start']:
                record.pages = None
                record.items = None
            elif self.liststats_datas:
                try:
                    data = self.liststats_datas[job['project']][job['spider']][job['job']]
                    record.pages = data['pages']  # Logparser: None or non-negative int
                    record.items = data['items']  # Logparser: None or non-negative int
                except KeyError:
                    pass
                except Exception as err:
                    self.logger.error(err)
            # SQLite DateTime type only accepts Python datetime and date objects as input
            record.update_time = datetime.now()  # datetime.now().replace(microsecond=0)
        # https://www.reddit.com/r/flask/comments/3tea4k/af_flasksqlalchemy_bulk_updateinsert/
        db.session.add_all(records)
        db.session.commit()

    def db_clean_pending_jobs(self):
        current_pending_jobs = [(job['project'], job['spider'], job['job'])
                                for job in self.jobs_backup if not job['start']]
        for record in self.Job.query.filter_by(start=None).all():
            if (record.project, record.spider, record.job) not in current_pending_jobs:
                db.session.delete(record)
                db.session.commit()
                self.logger.info("Deleted pending jobs %s", record)

    def query_jobs(self):
        current_running_job_pids = [int(job['pid']) for job in self.jobs_backup if job['pid']]
        self.logger.debug("current_running_job_pids: %s", current_running_job_pids)
        self.jobs_pagination = self.Job.query.filter_by(deleted=NOT_DELETED).order_by(
            self.Job.status.asc(), self.Job.finish.desc(), self.Job.start.asc(), self.Job.id.asc()).paginate(
            page=self.page, per_page=self.per_page, error_out=False)
        with db.session.no_autoflush:
            for index, job in enumerate(self.jobs_pagination.items,
                                        (self.jobs_pagination.page - 1) * self.jobs_pagination.per_page + 1):
                # print(vars(job))
                job.index = index
                job.pid = job.pid or ''
                job.start = job.start or ''  # None for Pending jobs
                job.runtime = job.runtime or ''
                job.finish = job.finish or ''  # None for Pending and Running jobs
                job.update_time = self.remove_microsecond(job.update_time)
                job.to_be_killed = True if job.pid and job.pid not in current_running_job_pids else False
                if job.finish:
                    job.url_multinode = url_for('servers', node=self.node, opt='schedule', project=job.project,
                                                version_job=self.DEFAULT_LATEST_VERSION, spider=job.spider)
                    job.url_action = url_for('schedule', node=self.node, project=job.project,
                                             version=self.DEFAULT_LATEST_VERSION, spider=job.spider)
                else:
                    job.url_multinode = url_for('servers', node=self.node, opt='stop', project=job.project,
                                                version_job=job.job)
                    job.url_action = url_for('api', node=self.node, opt='stop', project=job.project,
                                             version_spider_job=job.job)
                if job.start:
                    job.pages = self.NA if job.pages is None else job.pages  # May be 0
                    job.items = self.NA if job.items is None else job.items  # May be 0
                else:  # Pending
                    job.pages = None  # from Running/Finished to Pending
                    job.items = None
                    continue
                job_finished = 'True' if job.finish else None
                job.url_utf8 = url_for('log', node=self.node, opt='utf8', project=job.project, ui=self.UI,
                                       spider=job.spider, job=job.job, job_finished=job_finished)
                job.url_stats = url_for('log', node=self.node, opt='stats', project=job.project, ui=self.UI,
                                        spider=job.spider, job=job.job, job_finished=job_finished)
                job.url_clusterreports = url_for('clusterreports', node=self.node, project=job.project,
                                                 spider=job.spider, job=job.job)
                # '/items/demo/test/2018-10-12_205507.log'
                job.url_source = urljoin(self.public_url or self.url, job.href_log)
                if job.href_items:
                    job.url_items = urljoin(self.public_url or self.url, job.href_items)
                else:
                    job.url_items = ''
                job.url_delete = url_for('jobs.xhr', node=self.node, action='delete', id=job.id)

    def set_jobs_dict(self):
        for job in self.jobs_pagination.items:  # Pagination obj in handle_jobs_with_db() > query_jobs()
            key = '%s/%s/%s' % (job.project, job.spider, job.job)
            value = dict((k, v) for (k, v) in job.__dict__.items() if not k.startswith('_'))
            for k, v in value.items():
                if k in ['create_time', 'update_time', 'start', 'finish']:
                    value[k] = str(value[k])
            self.jobs_dict[key] = value

    def handle_jobs_without_db(self):
        for job in self.jobs:
            job['start'] = job['start'][5:]
            job['finish'] = job['finish'][5:]
            if not job['start']:
                self.pending_jobs.append(job)
            else:
                if job['finish']:
                    self.finished_jobs.append(job)
                    job['url_multinode_run'] = url_for('servers', node=self.node, opt='schedule',
                                                       project=job['project'], version_job=self.DEFAULT_LATEST_VERSION,
                                                       spider=job['spider'])
                    job['url_schedule'] = url_for('schedule', node=self.node, project=job['project'],
                                                  version=self.DEFAULT_LATEST_VERSION, spider=job['spider'])
                    job['url_start'] = url_for('api', node=self.node, opt='start', project=job['project'],
                                               version_spider_job=job['spider'])
                else:
                    self.running_jobs.append(job)
                    job['url_forcestop'] = url_for('api', node=self.node, opt='forcestop', project=job['project'],
                                                   version_spider_job=job['job'])

                job_finished = 'True' if job['finish'] else None
                job['url_utf8'] = url_for('log', node=self.node, opt='utf8', project=job['project'], ui=self.UI,
                                          spider=job['spider'], job=job['job'], job_finished=job_finished)
                job['url_stats'] = url_for('log', node=self.node, opt='stats', project=job['project'], ui=self.UI,
                                           spider=job['spider'], job=job['job'], job_finished=job_finished)
                job['url_clusterreports'] = url_for('clusterreports', node=self.node, project=job['project'],
                                                    spider=job['spider'], job=job['job'])
                # <a href='/items/demo/test/2018-10-12_205507.jl'>Items</a>
                m = re.search(HREF_PATTERN, job['href_items'])
                if m:
                    job['url_items'] = urljoin(self.public_url or self.url, m.group(1))
                else:
                    job['url_items'] = ''

            if not job['finish']:
                job['url_multinode_stop'] = url_for('servers', node=self.node, opt='stop', project=job['project'],
                                                    version_job=job['job'])
                job['url_stop'] = url_for('api', node=self.node, opt='stop', project=job['project'],
                                          version_spider_job=job['job'])

    def set_kwargs(self):
        self.kwargs = dict(
            node=self.node,
            url=self.url,
            url_schedule=url_for('schedule', node=self.node),
            url_liststats=url_for('api', node=self.node, opt='liststats'),
            url_liststats_source='http://%s/logs/stats.json' % self.SCRAPYD_SERVER,
            SCRAPYD_SERVER=self.SCRAPYD_SERVER.split(':')[0],
            LOGPARSER_VERSION=self.LOGPARSER_VERSION,
            JOBS_RELOAD_INTERVAL=self.JOBS_RELOAD_INTERVAL,
            IS_IE_EDGE=self.IS_IE_EDGE,
            pageview=self.metadata['pageview'],
            FEATURES=self.FEATURES
        )
        if self.style == 'database':
            self.kwargs.update(dict(
                url_jobs_classic=url_for('jobs', node=self.node, style='classic'),
                jobs=self.jobs_pagination
            ))
            return

        if self.JOBS_FINISHED_JOBS_LIMIT > 0:
            self.finished_jobs = self.finished_jobs[::-1][:self.JOBS_FINISHED_JOBS_LIMIT]
        else:
            self.finished_jobs = self.finished_jobs[::-1]
        self.kwargs.update(dict(
            colspan=14,
            url_jobs_database=url_for('jobs', node=self.node, style='database'),
            pending_jobs=self.pending_jobs,
            running_jobs=self.running_jobs,
            finished_jobs=self.finished_jobs,
            SHOW_JOBS_JOB_COLUMN=self.SHOW_JOBS_JOB_COLUMN
        ))


class JobsXhrView(BaseView):
    metadata = metadata

    def __init__(self):
        super(JobsXhrView, self).__init__()

        self.action = self.view_args['action']  # delete
        self.id = self.view_args['id']  # <int:id>

        self.js = {}
        self.Job = jobs_table_map[self.node]  # database class Job

    def dispatch_request(self, **kwargs):
        job = self.Job.query.get(self.id)
        if job:
            try:
                job.deleted = DELETED
                db.session.commit()
            except Exception as err:
                self.logger.error(traceback.format_exc())
                db.session.rollback()
                self.js['status'] = self.ERROR
                self.js['message'] = str(err)
            else:
                self.js['status'] = self.OK
                self.logger.info(self.js.setdefault('tip', "Deleted %s" % job))
        else:
            self.js['status'] = self.ERROR
            self.js['message'] = "job #%s not found in the database" % self.id

        return self.json_dumps(self.js, as_response=True)
