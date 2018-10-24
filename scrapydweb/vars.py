# coding: utf8
import os
import re

CWD = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(CWD, 'data')
UPLOAD_PATH = os.path.join(CWD, 'data/upload')
CACHE_PATH = os.path.join(CWD, 'data/cache')
DEPLOY_PATH = os.path.join(CWD, 'data/deploy')
SCHEDULE_PATH = os.path.join(CWD, 'data/schedule')
DEMO_PROJECTS_PATH = os.path.join(CWD, 'data', 'demo_projects')

for p in [DATA_PATH, UPLOAD_PATH, CACHE_PATH, DEPLOY_PATH, SCHEDULE_PATH, DEMO_PROJECTS_PATH]:
    if not os.path.isdir(p):
        os.mkdir(p)

INFO = 'info'
WARN = 'warning'
DEFAULT_LATEST_VERSION = "default: the latest version"


UA_DICT = {
    'chrome': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
    'iOS': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1',
    'iPad': 'Mozilla/5.0 (iPad; CPU OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1',
    'Android': 'Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Mobile Safari/537.36',
}


# For log.py
ALLOWED_SCRAPYD_LOG_EXTENSIONS = ['.log', '.log.gz', '.gz', '.txt', '']


# For run.py
# r'^(?:(?:(.*?)\:)(?:(.*?)@))?(.*?)(?:\:(.*?))?(?:#(.*?))?$'
pattern_scrapyd_server = re.compile(r"""
                        ^
                        (?:
                            (?:(.*?)\:)     # username:
                            (?:(.*?)@)      # password@
                        )?
                        (.*?)               # ip
                        (?:\:(.*?))?        # :port
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
