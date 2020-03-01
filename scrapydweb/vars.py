# coding: utf-8
import glob
import importlib
import io
import os
import re
import sys

from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING, STATE_STOPPED

from .default_settings import DATA_PATH as default_data_path
from .default_settings import DATABASE_URL as default_database_url
from .utils.setup_database import setup_database


PYTHON_VERSION = '.'.join([str(n) for n in sys.version_info[:3]])
PY2 = sys.version_info.major < 3
SCRAPYDWEB_SETTINGS_PY = 'scrapydweb_settings_v10.py'
sys.path.append(os.getcwd())
try:
    custom_settings_module = importlib.import_module(os.path.splitext(SCRAPYDWEB_SETTINGS_PY)[0])
except ImportError:
    custom_data_path = ''
    custom_database_url = ''
else:
    custom_data_path = getattr(custom_settings_module, 'DATA_PATH', '')
    custom_data_path = custom_data_path if isinstance(custom_data_path, str) else ''
    custom_database_url = getattr(custom_settings_module, 'DATABASE_URL', '')
    custom_database_url = custom_database_url if isinstance(custom_database_url, str) else ''

# For data storage
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = default_data_path or custom_data_path
if DATA_PATH:
    DATA_PATH = os.path.abspath(DATA_PATH)
else:
    DATA_PATH = os.path.join(ROOT_DIR, 'data')

DATABASE_PATH = os.path.join(DATA_PATH, 'database')
DEMO_PROJECTS_PATH = os.path.join(DATA_PATH, 'demo_projects')
DEPLOY_PATH = os.path.join(DATA_PATH, 'deploy')
HISTORY_LOG = os.path.join(DATA_PATH, 'history_log')
PARSE_PATH = os.path.join(DATA_PATH, 'parse')
SCHEDULE_PATH = os.path.join(DATA_PATH, 'schedule')
STATS_PATH = os.path.join(DATA_PATH, 'stats')

for path in [DATA_PATH, DATABASE_PATH, DEMO_PROJECTS_PATH, DEPLOY_PATH,
             HISTORY_LOG, PARSE_PATH, SCHEDULE_PATH, STATS_PATH]:
    if not os.path.isdir(path):
        os.mkdir(path)
    elif path in [PARSE_PATH, DEPLOY_PATH, SCHEDULE_PATH]:
        for file in glob.glob(os.path.join(path, '*.*')):
            if not os.path.split(file)[-1] in ['ScrapydWeb_demo.log']:
                os.remove(file)

RUN_SPIDER_HISTORY_LOG = os.path.join(HISTORY_LOG, 'run_spider_history.log')
TIMER_TASKS_HISTORY_LOG = os.path.join(HISTORY_LOG, 'timer_tasks_history.log')

# For database
DATABASE_URL = custom_database_url or default_database_url or 'sqlite:///' + DATABASE_PATH
results = setup_database(DATABASE_URL, DATABASE_PATH)
APSCHEDULER_DATABASE_URI, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_BINDS, DATABASE_PATH = results

# For check_app_config() and BaseView
ALLOWED_SCRAPYD_LOG_EXTENSIONS = ['.log', '.log.gz', '.txt', '.gz', '']
ALERT_TRIGGER_KEYS = ['CRITICAL', 'ERROR', 'WARNING', 'REDIRECT', 'RETRY', 'IGNORE']

# Error: Project names must begin with a letter and contain only letters, numbers and underscores
STRICT_NAME_PATTERN = re.compile(r'[^0-9A-Za-z_]')
LEGAL_NAME_PATTERN = re.compile(r'[^0-9A-Za-z_-]')

# For ScheduleView
SCHEDULE_ADDITIONAL = "-d setting=CLOSESPIDER_TIMEOUT=60\r\n-d setting=CLOSESPIDER_PAGECOUNT=10\r\n-d arg1=val1"
UA_DICT = {
    'custom': "Mozilla/5.0",
    'Chrome': ("Mozilla/5.0 (Windows NT 10.0; WOW64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36"),
    'iPhone': ("Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) "
               "AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"),
    'iPad': ("Mozilla/5.0 (iPad; CPU OS 12_1_4 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1"),
    'Android': ("Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2 XL Build/OPD1.170816.004) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Mobile Safari/537.36")
}

# For LogsView and ItemsView
DIRECTORY_PATTERN = re.compile(r"""
                                    <tr\sclass="(?P<odd_even>odd|even)">\n
                                        \s+<td>(?P<filename>.*?)</td>\n
                                        \s+<td>(?P<size>.*?)</td>\n
                                        \s+<td>(?P<content_type>.*?)</td>\n
                                        \s+<td>(?P<content_encoding>.*?)</td>\n
                                    </tr>
                                """, re.X)
DIRECTORY_KEYS = ['odd_even', 'filename', 'size', 'content_type', 'content_encoding']
HREF_NAME_PATTERN = re.compile(r'href="(.+?)">(.+?)<')

# For JobsView
jobs_table_map = {}

# For Timer Tasks
# STATE_STOPPED = 0, STATE_RUNNING = 1, STATE_PAUSED = 2
SCHEDULER_STATE_DICT = {
    STATE_STOPPED: 'STATE_STOPPED',
    STATE_RUNNING: 'STATE_RUNNING',
    STATE_PAUSED: 'STATE_PAUSED',
}


def setup_logfile(delete=False):
    if delete:
        for logfile in [RUN_SPIDER_HISTORY_LOG, TIMER_TASKS_HISTORY_LOG]:
            if os.path.exists(logfile):
                os.remove(logfile)

    if not os.path.exists(RUN_SPIDER_HISTORY_LOG):
        with io.open(RUN_SPIDER_HISTORY_LOG, 'w', encoding='utf-8') as f:
            f.write(u'%s\n%s' % ('#' * 50, RUN_SPIDER_HISTORY_LOG))

    if not os.path.exists(TIMER_TASKS_HISTORY_LOG):
        with io.open(TIMER_TASKS_HISTORY_LOG, 'w', encoding='utf-8') as f:
            f.write(u'%s\n%s\n\n' % (TIMER_TASKS_HISTORY_LOG, '#' * 50))


setup_logfile(delete=False)
