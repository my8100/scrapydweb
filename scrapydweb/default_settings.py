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

# Support multinode, default port would be 6800 if not provided,
# and group info is optional
SCRAPYD_SERVERS = [
    '127.0.0.1:6800',
    '192.168.0.101:6801@group1',
]

# Set to speed up loading utf8 and stats html
# e.g. C:/Users/username/logs/ or /home/username/logs/ ,
# The setting takes effect only when both ScrapydWeb and Scrapyd run on the same machine,
# and the Scrapyd server ip is added as '127.0.0.1'.
# See 'https://scrapyd.readthedocs.io/en/stable/config.html#logs-dir'
# to find out where the Scrapy logs are stored."
SCRAPYD_LOGS_DIR = ''

# Set True to disable caching utf8 and stats files in the background periodically
DISABLE_CACHE = False
# Set the interval while caching utf8 and stats files
CACHE_INTERVAL_SECONDS = 300
# Set True to delete cached utf8 and stats files at startup
DELETE_CACHE = False
