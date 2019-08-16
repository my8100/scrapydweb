# coding: utf-8
import atexit
import logging
from pprint import pformat

from apscheduler.events import EVENT_JOB_MAX_INSTANCES, EVENT_JOB_REMOVED
from apscheduler.executors.pool import ThreadPoolExecutor  # , ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from ..common import handle_metadata
from ..vars import APSCHEDULER_DATABASE_URI, TIMER_TASKS_HISTORY_LOG


apscheduler_logger = logging.getLogger('apscheduler')
# _handler = logging.StreamHandler()
# logging.FileHandler(filename, mode='a', encoding=None, delay=False)
_handler = logging.FileHandler(TIMER_TASKS_HISTORY_LOG, mode='a', encoding='utf-8')
_handler.setLevel(logging.WARNING)
_formatter = logging.Formatter(fmt="[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
_handler.setFormatter(_formatter)
apscheduler_logger.addHandler(_handler)


# EVENT_JOB_REMOVED = 2 ** 10
# {'alias': None, 'code': 1024, 'job_id': '1', 'jobstore': 'default'}
# EVENT_JOB_MAX_INSTANCES = 2 ** 16
EVENT_MAP = {EVENT_JOB_MAX_INSTANCES: 'EVENT_JOB_MAX_INSTANCES', EVENT_JOB_REMOVED: 'EVENT_JOB_REMOVED'}

jobstores = {
    'default': SQLAlchemyJobStore(url=APSCHEDULER_DATABASE_URI),
    'memory': MemoryJobStore()
}
executors = {
    'default': ThreadPoolExecutor(20),
    # 'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': True,
    'max_instances': 1
}
# https://apscheduler.readthedocs.io/en/latest/userguide.html
# scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)
scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)


# https://apscheduler.readthedocs.io/en/latest/userguide.html#scheduler-events
# EVENT_JOB_EXECUTED: 'code': 4096, 'exception': None
# EVENT_JOB_ERROR: 'code': 8192, 'exception': xxx
# apscheduler/executors/base.py
    # events.append(JobExecutionEvent(EVENT_JOB_MISSED, job.id, jobstore_alias,
    #                                 run_time))
    # logger.warning('Run time of job "%s" was missed by %s', job, difference)
# WARNING in apscheduler.executors.default: Run time of job "task_1" was missed by 0:00:26.030600
# apscheduler/schedulers/base.py
#     self._logger = maybe_ref(config.pop('logger', None)) or getLogger('apscheduler.scheduler')
#     self._logger.warning(
#         'Execution of job "%s" skipped: maximum number of running '
#         'instances reached (%d)', job, job.max_instances)
#     event = JobSubmissionEvent(EVENT_JOB_MAX_INSTANCES, job.id,
#                                jobstore_alias, run_times)
#     events.append(event)

# EVENT_JOB_MAX_INSTANCES: 'job_id': 'jobs_snapshot', 'jobstore': 'memory',
# WARNING in apscheduler.scheduler: Execution of job "create_jobs_snapshot (trigger: interval[0:00:10],
# next run at: " skipped: maximum number of running instances reached (1)
def my_listener(event):
    msg = "%s: \n%s\n" % (EVENT_MAP[event.code], pformat(vars(event), indent=4))
    # logger defined outside the callback of add_listener does not take effect?!
    # In case JOBS_SNAPSHOT_INTERVAL is set too short, like 10 seconds
    if event.jobstore != 'default':
        logging.getLogger('apscheduler').info(msg)
    else:
        logging.getLogger('apscheduler').warning(msg)

    # if hasattr(event, 'exception') and event.exception:
    #     print(event.exception)
    # if hasattr(event, 'traceback') and event.traceback:
    #     print(event.traceback)


# To trigger EVENT_JOB_MAX_INSTANCES:
#   add sleep in execute_task()
#   second: */10, max_instances: 2
# EVENT_JOB_ERROR and EVENT_JOB_MISSED are caught by logging.FileHandler
scheduler.add_listener(my_listener, EVENT_JOB_MAX_INSTANCES | EVENT_JOB_REMOVED)

# if scheduler.state == STATE_STOPPED:
scheduler.start(paused=True)


def shutdown_scheduler():
    apscheduler_logger.debug("Scheduled tasks: %s", scheduler.get_jobs())
    apscheduler_logger.warning("Shutting down the scheduler for timer tasks gracefully, "
                               "wait until all currently executing tasks are finished")
    apscheduler_logger.warning("The main pid is %s. Kill it manually if you don't want to wait",
                               handle_metadata().get('main_pid'))
    scheduler.shutdown()
    # apscheduler_logger.info("Waits until all currently executing jobs are finished. "
    #                         "Press CTRL+C to force unclean shutdown")
    # try:
    #     scheduler.shutdown()
    # except KeyboardInterrupt:
    #     apscheduler_logger.warning("Forcing unclean shutdown")
    #     scheduler.shutdown(wait=False)
    # apscheduler_logger.info("Good Bye")


# https://stackoverflow.com/questions/21214270/scheduling-a-function-to-run-every-hour-on-flask
atexit.register(lambda: shutdown_scheduler())
