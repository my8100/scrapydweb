# coding: utf8
"""
BROWSER_HOST >>> SCRAPYDWEB_HOST:SCRAPYDWEB_PORT >>> SCRAPYD_SERVERS
Run 'scrapydweb -h' or check 'scrapydweb/run.py' to get help
"""


# Set True to enable debug mode and debugger would be available in the browser
DEBUG = False


# '0.0.0.0' makes ScrapydWeb server visible externally, set '127.0.0.1' to disable that
SCRAPYDWEB_HOST = '0.0.0.0'
SCRAPYDWEB_PORT = 5000

# Basic auth for web UI
# The setting takes effect only when both USERNAME and PASSWORD are not empty string
# USERNAME = 'admin'
# PASSWORD = '12345'


# Support Multinode Scrapyd servers
    # string format: username:password@ip:port#group
        # default port would be 6800 if not provided,
        # basic auth and group info are both optional.
        # e.g., '127.0.0.1' or 'username:password@192.168.123.123:6801#group'
    # tuple format: (username, password, ip, port, group)
        # If username or password or group info is too complicated (e.g., contains ':@#'),
        # or if ScrapydWeb fails to parse the string format passed in,
        # it's better to pass in a 5 elements tuple
        # e.g., ('', '', '127.0.0.1', '', '') or ('username', 'password', '192.168.123.123', '6801', 'group')
SCRAPYD_SERVERS = [
    '127.0.0.1',
    # 'username:password@localhost:6801#group',

    # ('', '', '127.0.0.1', '', ''),
    ('username', 'password', 'localhost', '6801', 'group'),
]

# Set to speed up loading utf8 and stats html
# e.g. C:/Users/username/logs/ or /home/username/logs/ ,
# The setting takes effect only when both ScrapydWeb and Scrapyd run on the same machine,
# and the Scrapyd server ip is added as '127.0.0.1'.
# See 'https://scrapyd.readthedocs.io/en/stable/config.html#logs-dir'
# to find out where the Scrapy logs are stored."
SCRAPYD_LOGS_DIR = ''

# The extension used to locate scrapy log in dashboard, and the order matters
SCRAPYD_LOG_EXTENSIONS = ['.log', '.log.gz', '.gz', '.txt', '']

# Set True to hide Items page and Items column in Dashboard page
HIDE_SCRAPYD_ITEMS = False

# Set True to show jobid in Dashboard page
SHOW_DASHBOARD_JOB_COLUMN = False


# Set True to disable caching utf8 and stats files in the background periodically
DISABLE_CACHE = False
# Sleep seconds between the end of last round of caching and the start of next round
CACHE_ROUND_INTERVAL = 300
# Sleep seconds between every request while caching
CACHE_REQUEST_INTERVAL = 10
# Set True to delete cached utf8 and stats files at startup
DELETE_CACHE = False
