# coding: utf8
import os
import io
import time
import glob
import re


CWD = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(CWD, 'data')
PARSE_PATH = os.path.join(DATA_PATH, 'parse')
CACHE_PATH = os.path.join(DATA_PATH, 'cache')
DEPLOY_PATH = os.path.join(DATA_PATH, 'deploy')
SCHEDULE_PATH = os.path.join(DATA_PATH, 'schedule')
DEMO_PROJECTS_PATH = os.path.join(DATA_PATH, 'demo_projects')

for p in [DATA_PATH, PARSE_PATH, CACHE_PATH, DEPLOY_PATH, SCHEDULE_PATH, DEMO_PROJECTS_PATH]:
    if not os.path.isdir(p):
        os.mkdir(p)
    elif p in [PARSE_PATH, DEPLOY_PATH, SCHEDULE_PATH]:
        for file in glob.glob(os.path.join(p, '*.*')):
            if not os.path.split(file)[-1] in ['demo.txt', 'history.log']:
                os.remove(file)


LAST_CHECK_UPDATE = os.path.join(DATA_PATH, 'last_check_update')

try:
    if not os.path.exists(LAST_CHECK_UPDATE):
        with io.open(LAST_CHECK_UPDATE, 'w') as f:
            f.write(u'{:.0f}'.format(time.time()))
        CHECK_UPDATE = True
    else:
        with io.open(LAST_CHECK_UPDATE, 'r+') as f:
            if time.time() - int(f.read()) > 3600 * 24 * 7:
                f.seek(0)
                f.write(u'{:.0f}'.format(time.time()))
                CHECK_UPDATE = True
            else:
                CHECK_UPDATE = False
except:
    try:
        os.remove(LAST_CHECK_UPDATE)
    except:
        pass
    CHECK_UPDATE = True


INFO = 'info'
WARN = 'warning'
DEFAULT_LATEST_VERSION = "default: the latest version"


UA_DICT = {
    'chrome': ("Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"),
    'iOS': ("Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) "
            "AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1"),
    'iPad': ("Mozilla/5.0 (iPad; CPU OS 9_1 like Mac OS X) "
             "AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1"),
    'Android': ("Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Mobile Safari/537.36")
}


# For log.py
ALLOWED_SCRAPYD_LOG_EXTENSIONS = ['.log', '.log.gz', '.txt', '.gz', '']


# For run.py
# r'^(?:(?:(.*?)\:)(?:(.*?)@))?(.*?)(?:\:(.*?))?(?:#(.*?))?$'
pattern_scrapyd_server = re.compile(r"""
                        ^
                        (?:
                            (?:(.*?):)     # username:
                            (?:(.*?)@)      # password@
                        )?
                        (.*?)               # ip
                        (?::(.*?))?        # :port
                        (?:\#(.*?))?        # #group
                        $
                    """, re.X)


# For dashboard
pattern_jobs = re.compile(r"""<tr>
                        <td>(?P<Project>.*?)</td>
                        <td>(?P<Spider>.*?)</td>
                        <td>(?P<Job>.*?)</td>
                        (?:<td>(?P<PID>.*?)</td>)?
                        (?:<td>(?P<Start>.*?)</td>)?
                        (?:<td>(?P<Runtime>.*?)</td>)?
                        (?:<td>(?P<Finish>.*?)</td>)?
                        (?:<td>(?P<Log>.*?)</td>)?
                        (?:<td>(?P<Items>.*?)</td>)?
                        </tr>
                    """, re.X)
keys_jobs = ['project', 'spider', 'job', 'pid', 'start', 'runtime', 'finish', 'log', 'items']


# For directory
pattern_directory = re.compile(r"""<tr\sclass="(?P<odd_even>odd|even)">\n
                                   \s+<td>(?P<filename>.*?)</td>\n
                                   \s+<td>(?P<size>.*?)</td>\n
                                   \s+<td>(?P<content_type>.*?)</td>\n
                                   \s+<td>(?P<content_encoding>.*?)</td>\n
                                </tr>
                                """, re.X)

keys_directory = ['odd_even', 'filename', 'size', 'content_type', 'content_encoding']


# For email notice
EMAIL_CONTENT_KEYS = [
    'log_critical_count',
    'log_error_count',
    'log_warning_count',
    'log_redirect_count',
    'log_retry_count',
    'log_ignore_count',
    'crawled_pages',
    'scraped_items'
]

EMAIL_TRIGGER_KEYS = ['CRITICAL', 'ERROR', 'WARNING', 'REDIRECT', 'RETRY', 'IGNORE']
