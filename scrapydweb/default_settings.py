# coding: utf8
"""
How ScrapydWeb works:
BROWSER_HOST <<<>>> SCRAPYDWEB_BIND:SCRAPYDWEB_PORT <<<>>> SCRAPYD_SERVERS

Run 'scrapydweb -h' to get help and a config file named 'scrapydweb_settings_vN.py' (N for a number)
would be copied to current working directory, then you can custom settings in it.

Note that 'scrapydweb_settings_vN.py' may contain only a portion of setting items of 'default_settings.py',
you may check out here to get the latest version of default_settings.py:
https://github.com/my8100/scrapydweb/blob/master/scrapydweb/default_settings.py
"""


############################## ScrapydWeb ################################


# '0.0.0.0' makes ScrapydWeb server visible externally, set SCRAPYDWEB_BIND to '127.0.0.1' to disable that.
SCRAPYDWEB_BIND = '0.0.0.0'
SCRAPYDWEB_PORT = 5000

# Enable basic auth for web UI.
# The setting takes effect only when both USERNAME and PASSWORD are non-empty string.
USERNAME = ''
PASSWORD = ''


############################## Scrapy ####################################


# Set to enable auto eggifying in Deploy page,
# e.g., 'C:/Users/username/myprojects/' or '/home/username/myprojects/'
SCRAPY_PROJECTS_DIR = ''


############################## Scrapyd ###################################


# Support Multinode Scrapyd servers
    # string format: username:password@ip:port#group
        # default port would be 6800 if not provided,
        # basic auth and group info are both optional.
        # e.g., '127.0.0.1' or 'username:password@192.168.123.123:6801#group'

    # tuple format: (username, password, ip, port, group)
        # When username or password or group info is too complicated (e.g., contains ':@#'),
        # or if ScrapydWeb fails to parse the string format passed in,
        # it's recommended to pass in a 5 elements tuple
        # e.g., ('', '', '127.0.0.1', '', '') or ('username', 'password', '192.168.123.123', '6801', 'group')
SCRAPYD_SERVERS = [
    '127.0.0.1',
    # 'username:password@localhost:6801#group',

    # ('', '', '127.0.0.1', '', ''),
    ('username', 'password', 'localhost', '6801', 'group'),
]

# Set to speed up loading utf8 and stats html.
# e.g., 'C:/Users/username/logs/' or '/home/username/logs/'
# The setting takes effect only when both ScrapydWeb and Scrapyd run on the same machine,
# and the Scrapyd server ip is added as '127.0.0.1'.
# Check out here to find out where the Scrapy logs are stored:
# https://scrapyd.readthedocs.io/en/stable/config.html#logs-dir
SCRAPYD_LOGS_DIR = ''

# The extension used to locate scrapy log in dashboard, and the order matters.
SCRAPYD_LOG_EXTENSIONS = ['.log', '.log.gz', '.gz', '.txt', '']


############################## Page display ##############################


# Set True to enable debug mode and debugger would be available in the browser.
# Actually, it's not recommended to turn on debug mode, also no need,
# since its side-effects includes creating two caching subprocess in the background.
DEBUG = False

# Set True to show Items page and Items column in Dashboard page
SHOW_SCRAPYD_ITEMS = True

# Set True to show jobid in Dashboard page
SHOW_DASHBOARD_JOB_COLUMN = False

# Dashboard page would auto reload every N seconds.
# Set 0 to disable auto reloading.
DASHBORAD_RELOAD_INTERVAL = 300

# Refresh daemonstatus of the current Scrapyd server at every N seconds,
# which is displayed in the top right corner.
# Set 0 to disable auto refreshing.
DAEMONSTATUS_REFRESH_INTERVAL = 10


############################## Html caching ##############################


# Set True to disable caching utf8 and stats files in the background periodically
DISABLE_CACHE = False

# Set True to delete cached utf8 and stats files at startup
DELETE_CACHE = False

# Sleep seconds between the end of last round of caching and the start of next round
CACHE_ROUND_INTERVAL = 300

# Sleep seconds between every request while caching
CACHE_REQUEST_INTERVAL = 10
