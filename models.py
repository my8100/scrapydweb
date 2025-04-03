# coding: utf-8
from datetime import datetime
from pprint import pformat
import time

from flask_sqlalchemy import SQLAlchemy

from .vars import STATE_RUNNING


db = SQLAlchemy(session_options=dict(autocommit=False, autoflush=True))


# TODO: Database Migrations https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database
# http://flask-sqlalchemy.pocoo.org/2.3/binds/#binds
class Metadata(db.Model):
    __tablename__ = 'metadata'
    __bind_key__ = 'metadata'

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(20), unique=True, nullable=False)
    last_check_update_timestamp = db.Column(db.Float, unique=False, default=time.time)
    main_pid = db.Column(db.Integer, unique=False, nullable=True)
    logparser_pid = db.Column(db.Integer, unique=False, nullable=True)
    poll_pid = db.Column(db.Integer, unique=False, nullable=True)
    pageview = db.Column(db.Integer, unique=False, nullable=False, default=0)
    url_scrapydweb = db.Column(db.Text(), unique=False, nullable=False, default='http://127.0.0.1:5000')
    url_jobs = db.Column(db.String(255), unique=False, nullable=False, default='/1/jobs/')
    url_schedule_task = db.Column(db.String(255), unique=False, nullable=False, default='/1/schedule/task/')
    url_delete_task_result = db.Column(db.String(255), unique=False, nullable=False, default='/1/tasks/xhr/delete/1/1/')
    username = db.Column(db.String(255), unique=False, nullable=True)
    password = db.Column(db.String(255), unique=False, nullable=True)
    scheduler_state = db.Column(db.Integer, unique=False, nullable=False, default=STATE_RUNNING)
    jobs_per_page = db.Column(db.Integer, unique=False, nullable=False, default=100)
    tasks_per_page = db.Column(db.Integer, unique=False, nullable=False, default=100)
    jobs_style = db.Column(db.String(8), unique=False, nullable=False, default='database')  # 'classic'

    def __repr__(self):
        return pformat(vars(self))


# TODO: Timezone Conversions https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xii-dates-and-times
def create_jobs_table(server):
    class Job(db.Model):
        __tablename__ = server
        __bind_key__ = 'jobs'
        # https://stackoverflow.com/questions/10059345/sqlalchemy-unique-across-multiple-columns
        # https://stackoverflow.com/questions/43975349/why-uniqueconstraint-doesnt-work-in-flask-sqlalchemy
        __table_args__ = (db.UniqueConstraint('project', 'spider', 'job'), )

        id = db.Column(db.Integer, primary_key=True)
        project = db.Column(db.String(255), unique=False, nullable=False)  # Pending
        spider = db.Column(db.String(255), unique=False, nullable=False)  # Pending
        job = db.Column(db.String(255), unique=False, nullable=False)  # Pending
        status = db.Column(db.String(1), unique=False, nullable=False, index=True)  # Pending 0, Running 1, Finished 2
        deleted = db.Column(db.String(1), unique=False, nullable=False, default='0', index=True)
        create_time = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now)
        update_time = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now)

        pages = db.Column(db.Integer, unique=False, nullable=True)
        items = db.Column(db.Integer, unique=False, nullable=True)
        pid = db.Column(db.Integer, unique=False, nullable=True)  # Running
        start = db.Column(db.DateTime, unique=False, nullable=True, index=True)
        runtime = db.Column(db.String(20), unique=False, nullable=True)
        finish = db.Column(db.DateTime, unique=False, nullable=True, index=True)  # Finished
        href_log = db.Column(db.Text(), unique=False, nullable=True)
        href_items = db.Column(db.Text(), unique=False, nullable=True)

        def __repr__(self):
            return "<Job #%s in table %s, %s/%s/%s start: %s>" % (
                self.id, self.__tablename__, self.project, self.spider, self.job, self.start)

    return Job
    # sqlalchemy/ext/declarative/clsregistry.py:128: SAWarning: This declarative base already contains a class
    # with the same class name and module name as scrapydweb.models.Job,
    # and will be replaced in the string-lookup table.
    # https://stackoverflow.com/questions/27773489/dynamically-create-a-python-subclass-in-a-function
    # return type('Job_%s' % server, (Job, ), dict(__tablename__=server,  __bind_key__='jobs'))

# print(dir([create_table(s) for s in 'abc'][0]))


# http://flask-sqlalchemy.pocoo.org/2.3/models/    One-to-Many Relationships
# https://techarena51.com/blog/one-to-many-relationships-with-flask-sqlalchemy/
# https://docs.sqlalchemy.org/en/latest/orm/cascades.html#delete-orphan
# https://docs.sqlalchemy.org/en/latest/core/constraints.html#indexes
# https://stackoverflow.com/questions/14419299/adding-indexes-to-sqlalchemy-models-after-table-creation
# https://stackoverflow.com/questions/8890738/sqlalchemy-does-column-with-foreignkey-creates-index-automatically
class Task(db.Model):
    __tablename__ = 'task'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False, nullable=True)  # None
    trigger = db.Column(db.String(8), unique=False, nullable=False)  # cron, interval, date
    create_time = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now)  # datetime.utcnow
    update_time = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now)

    project = db.Column(db.String(255), unique=False, nullable=False)
    version = db.Column(db.String(255), unique=False, nullable=False)
    spider = db.Column(db.String(255), unique=False, nullable=False)
    jobid = db.Column(db.String(255), unique=False, nullable=False)
    settings_arguments = db.Column(db.Text(), unique=False, nullable=False)
    selected_nodes = db.Column(db.Text(), unique=False, nullable=False)

    year = db.Column(db.String(255), unique=False, nullable=False)
    month = db.Column(db.String(255), unique=False, nullable=False)
    day = db.Column(db.String(255), unique=False, nullable=False)
    week = db.Column(db.String(255), unique=False, nullable=False)
    day_of_week = db.Column(db.String(255), unique=False, nullable=False)
    hour = db.Column(db.String(255), unique=False, nullable=False)
    minute = db.Column(db.String(255), unique=False, nullable=False)
    second = db.Column(db.String(255), unique=False, nullable=False)

    start_date = db.Column(db.String(19), unique=False, nullable=True)  # '2019-01-01 00:00:01'     None
    end_date = db.Column(db.String(19), unique=False, nullable=True)  # '2019-01-01 00:00:01'       None

    timezone = db.Column(db.String(255), unique=False, nullable=True)  # None
    jitter = db.Column(db.Integer, unique=False, nullable=False)  # int
    misfire_grace_time = db.Column(db.Integer, unique=False, nullable=True)  # None|a positive integer
    coalesce = db.Column(db.String(5), unique=False, nullable=False)  # 'True'|'False'
    max_instances = db.Column(db.Integer, unique=False, nullable=False)  # int

    results = db.relationship('TaskResult', backref='task', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return "<Task #%s (%s), %s/%s/%s/%s, created at %s, updated at %s>" % (
                self.id, self.name, self.project, self.version, self.spider, self.jobid,
                self.create_time, self.update_time)


class TaskResult(db.Model):
    __tablename__ = 'task_result'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False, index=True)
    execute_time = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now)
    fail_count = db.Column(db.Integer, unique=False, nullable=False, default=0)
    pass_count = db.Column(db.Integer, unique=False, nullable=False, default=0)

    results = db.relationship('TaskJobResult', backref='task_result', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return "<TaskResult #%s of task #%s (%s), [FAIL %s, PASS %s], executed at %s>" % (
                self.id, self.task_id, self.task.name, self.fail_count, self.pass_count, self.execute_time)


class TaskJobResult(db.Model):
    __tablename__ = 'task_job_result'

    id = db.Column(db.Integer, primary_key=True)
    task_result_id = db.Column(db.Integer, db.ForeignKey('task_result.id'), nullable=False, index=True)
    run_time = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now)
    node = db.Column(db.Integer, unique=False, nullable=False, index=True)
    server = db.Column(db.String(255), unique=False, nullable=False)  # '127.0.0.1:6800'
    status_code = db.Column(db.Integer, unique=False, nullable=False)  # -1, 200
    status = db.Column(db.String(9), unique=False, nullable=False)  # ok|error|exception
    # psycopg2.DataError) value too long for type character varying(1000)
    # https://docs.sqlalchemy.org/en/latest/core/type_basics.html#sqlalchemy.types.Text
    # In general, TEXT objects do not have a length
    result = db.Column(db.Text(), unique=False, nullable=False)  # jobid|message|exception

    def __repr__(self):
        kwargs = dict(
            task_id=self.task_result.task_id,
            task_name=self.task_result.task.name,
            project=self.task_result.task.project,
            version=self.task_result.task.version,
            spider=self.task_result.task.spider,
            jobid=self.task_result.task.jobid,
            run_time=str(self.run_time),  # TypeError: Object of type datetime is not JSON serializable
            node=self.node,
            server=self.server,
            status_code=self.status_code,
            status=self.status,
            result=self.result,
            task_result_id=self.task_result_id,
            id=self.id,
        )
        return '<TaskJobResult \n%s>' % pformat(kwargs, indent=4)
