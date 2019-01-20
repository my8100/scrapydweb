# coding: utf8
import glob
import os
import re

from .utils.utils import get_pageview_dict


ALLOWED_SCRAPYD_LOG_EXTENSIONS = ['.log', '.log.gz', '.txt', '.gz', '']
# For logs.py and items.py
DIRECTORY_PATTERN = re.compile(r"""
                                    <tr\sclass="(?P<odd_even>odd|even)">\n
                                        \s+<td>(?P<filename>.*?)</td>\n
                                        \s+<td>(?P<size>.*?)</td>\n
                                        \s+<td>(?P<content_type>.*?)</td>\n
                                        \s+<td>(?P<content_encoding>.*?)</td>\n
                                    </tr>
                                """, re.X)
DIRECTORY_KEYS = ['odd_even', 'filename', 'size', 'content_type', 'content_encoding']
# For check_app_config.py and MyView
EMAIL_TRIGGER_KEYS = ['CRITICAL', 'ERROR', 'WARNING', 'REDIRECT', 'RETRY', 'IGNORE']


CWD = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(CWD, 'data')
DEMO_PROJECTS_PATH = os.path.join(DATA_PATH, 'demo_projects')
DEPLOY_PATH = os.path.join(DATA_PATH, 'deploy')
PARSE_PATH = os.path.join(DATA_PATH, 'parse')
SCHEDULE_PATH = os.path.join(DATA_PATH, 'schedule')

for path in [DATA_PATH, DEMO_PROJECTS_PATH, DEPLOY_PATH, PARSE_PATH, SCHEDULE_PATH]:
    if not os.path.isdir(path):
        os.mkdir(path)
    elif path in [PARSE_PATH, DEPLOY_PATH, SCHEDULE_PATH]:
        for file in glob.glob(os.path.join(path, '*.*')):
            if not os.path.split(file)[-1] in ['ScrapydWeb_demo.log', 'history.log']:
                os.remove(file)


LAST_CHECK_UPDATE_PATH = os.path.join(DATA_PATH, 'LAST_CHECK_UPDATE_PATH')
pageview_dict = get_pageview_dict(LAST_CHECK_UPDATE_PATH)
