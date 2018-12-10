# coding: utf8
"""
How ScrapydWeb works:
BROWSER_HOST <<<>>> SCRAPYDWEB_BIND:SCRAPYDWEB_PORT <<<>>> SCRAPYD_SERVERS
"""

########################################################################
########################################################################
## QUICK SETUP: Simply search and update the SCRAPYD_SERVERS item, leave the rest as default.
## Recommended Reading: [How to efficiently manage your distributed web scraping projects]
## (https://medium.com/@my8100)
########################################################################
## 快速设置：搜索并更新 SCRAPYD_SERVERS 配置项即可，其余配置项保留默认值。
## 推荐阅读：[如何简单高效地部署和监控分布式爬虫项目]
## (https://juejin.im/post/5bebc5fd6fb9a04a053f3a0e)
########################################################################
########################################################################


############################## ScrapydWeb ##############################
# Set to '0.0.0.0' or IP-OF-CURRENT-HOST makes ScrapydWeb server visible externally,
# otherwise, set SCRAPYDWEB_BIND to '127.0.0.1'
SCRAPYDWEB_BIND = '0.0.0.0'
SCRAPYDWEB_PORT = 5000

# Set True to enable basic auth for web UI
ENABLE_AUTH = False
# In order to enable basic auth, both USERNAME and PASSWORD should be non-empty strings
USERNAME = ''
PASSWORD = ''


############################## Scrapy ##################################
# Set to enable auto eggifying in Deploy page,
# e.g., 'C:/Users/username/myprojects/' or '/home/username/myprojects/'
SCRAPY_PROJECTS_DIR = ''


############################## Scrapyd #################################
# Make sure that [Scrapyd](https://github.com/scrapy/scrapyd) has been installed and started on all of your hosts.
# Note that if you want to visit Scrapyd remotely,
# you have to manually set the [bind_address](https://scrapyd.readthedocs.io/en/latest/config.html#bind-address)
# to 'bind_address = 0.0.0.0' and restart Scrapyd to make it visible externally.
# ------------------------------------------------------------------------------------------------------------------
# 请先确保所有主机都已经安装和启动 [Scrapyd](https://github.com/scrapy/scrapyd) ，
# 如需远程访问 Scrapyd，则需将 Scrapyd 配置文件中的 [bind_address](https://scrapyd.readthedocs.io/en/latest/config.html#bind-address)
# 修改为 'bind_address = 0.0.0.0'，然后重启 Scrapyd。

# Support multiple Scrapyd servers:
# - string format: username:password@ip:port#group
#   - default port would be 6800 if not provided,
#   - basic auth and group info are both optional.
#   - e.g., '127.0.0.1' or 'username:password@192.168.123.123:6801#group'
# - tuple format: (username, password, ip, port, group)
#   - When username or password or group info is too complicated (e.g., contains ':@#'),
#   - or if ScrapydWeb fails to parse the string format passed in,
#   - it's recommended to pass in a tuple with 5 elements
#   - e.g., ('', '', '127.0.0.1', '', '') or ('username', 'password', '192.168.123.123', '6801', 'group')
SCRAPYD_SERVERS = [
    '127.0.0.1:6800',
    # 'username:password@localhost:6801#group',
    ('username', 'password', 'localhost', '6801', 'group'),
]

# Set to speed up loading scrapy logs.
# e.g., 'C:/Users/username/logs/' or '/home/username/logs/'
# The setting takes effect only when both ScrapydWeb and Scrapyd run on the same host,
# and the Scrapyd server ip is added as '127.0.0.1'.
# Check out below link to find out where the Scrapy logs are stored:
# https://scrapyd.readthedocs.io/en/stable/config.html#logs-dir
SCRAPYD_LOGS_DIR = ''

# The extension used to locate scrapy log in dashboard, and the order matters.
SCRAPYD_LOG_EXTENSIONS = ['.log', '.log.gz', '.txt']


############################## Page Display ############################
# Set True to show Items page and Items column in Dashboard page
SHOW_SCRAPYD_ITEMS = True

# Set True to show jobid in Dashboard page
SHOW_DASHBOARD_JOB_COLUMN = False

# Dashboard page would auto reload every N seconds.
# Set 0 to disable auto reloading.
DASHBOARD_RELOAD_INTERVAL = 300

# Refresh daemonstatus of the current Scrapyd server every N seconds,
# which is displayed in the top right corner.
# Set 0 to disable auto refreshing.
DAEMONSTATUS_REFRESH_INTERVAL = 10


############################## HTML Caching ############################
# Set False to disable caching HTML for Log and Stats page in the background periodically
ENABLE_CACHE = True

# Sleep seconds between the end of last round of caching and the start of next round
CACHE_ROUND_INTERVAL = 300

# Sleep seconds between every request while caching
CACHE_REQUEST_INTERVAL = 10

# Set True to delete cached HTML files of Log and Stats page at startup
DELETE_CACHE = False


############################## Email Notice ############################
# Keep in mind that "Email Notice" depends on "HTML Caching" to collect statistics,
# so you have to enable "HTML Caching" by setting "ENABLE_CACHE = True"
# before setting "ENABLE_EMAIL = True" (check out the "HTML Caching" section above).

# In order to be notified (and stop/forcestop a job when triggered) in time,
# you can reduce the value of CACHE_ROUND_INTERVAL (and CACHE_REQUEST_INTERVAL),
# at the cost of burdening both CPU and bandwidth of your servers.

# Tip: set SCRAPYDWEB_BIND to the actual IP of  your server, then you can visit ScrapydWeb via the links in the email.
# (check out the "ScrapydWeb" section above)

# Check out below link if you are using ECS of Alibaba Cloud and your SMTP server provides TCP port 25 only:
# https://www.alibabacloud.com/help/doc-detail/56130.htm
########################################################################
# Set True to enable email notice
ENABLE_EMAIL = False

############### smtp settings ###############
SMTP_SERVER = ''
SMTP_PORT = 0
SMTP_OVER_SSL = False

# Config for https://mail.google.com using SSL
# SMTP_SERVER = 'smtp.gmail.com'
# SMTP_PORT = 465
# SMTP_OVER_SSL = True

# Config for https://mail.google.com
# SMTP_SERVER = 'smtp.gmail.com'
# SMTP_PORT = 587
# SMTP_OVER_SSL = False

# Config for https://mail.qq.com/ using SSL
# SMTP_SERVER = 'smtp.qq.com'
# SMTP_PORT = 465
# SMTP_OVER_SSL = True

# Config for http://mail.10086.cn/
# SMTP_SERVER = 'smtp.139.com'
# SMTP_PORT = 25
# SMTP_OVER_SSL = False

# A timeout in seconds for the connection attempt
SMTP_CONNECTION_TIMEOUT = 10

############### sender & recipients ##########
# e.g., 'username@gmail.com'
FROM_ADDR = ''

# e.g., 'password4gmail'
# As for different email service provider, you might have to get an APP password (like Gmail)
# or an authorization code (like QQ mail) and set it as EMAIL_PASSWORD.
# Check out below links to get more help:
# https://stackoverflow.com/a/27515833/10517783 How to send an email with Gmail as provider using Python?
# https://stackoverflow.com/a/26053352/10517783 Python smtplib proxy support
EMAIL_PASSWORD = ''

# e.g., ['username@gmail.com', ]
TO_ADDRS = []

############### email working time ##########
# Monday is 1 and Sunday is 7
# e.g, [1, 2, 3, 4, 5, 6, 7]
EMAIL_WORKING_DAYS = []

# From 0 to 23
# e.g., [9] + list(range(15, 18)) >>> [9, 15, 16, 17], or range(24) for 24 hours
EMAIL_WORKING_HOURS = []

############### email triggers ##############
# Set 0 to disable trigger, otherwise, set a positive integer to trigger email notice every N seconds
ON_JOB_RUNNING_INTERVAL = 0

# Set True to enable trigger when job is finished
ON_JOB_FINISHED = False

# - LOG_XXX_THRESHOLD: Set 0 to disable trigger, otherwise, set a positive integer as the threshold
# for a specific kind of log. Then a corresponding email would be sent the first time reaching the threshold.
# - LOG_XXX_TRIGGER_STOP: Set True to stop current job automatically when reaching LOG_XXX_THRESHOLD.
# - LOG_XXX_TRIGGER_FORCESTOP: Set True to forcestop current job automatically when reaching LOG_XXX_THRESHOLD.

# Note that LOG_XXX_TRIGGER_STOP would send SIGTERM only one time and try to shut down the crawler gracefully.
# Whereas LOG_XXX_TRIGGER_FORCESTOP would force UNCLEAN shutdown, without Scrapy stats dumped!

# When LOG_XXX_THRESHOLD is set non-zero and both LOG_XXX_TRIGGER_STOP and LOG_XXX_TRIGGER_FORCESTOP are set False,
# a trigger email would be sent without executing 'STOP' or 'FORCESTOP'.
# When no LOG_XXX_TRIGGER_FORCESTOP is triggered, 'STOP' would be executed one time at most to avoid unclean shutdown,
# no matter how many LOG_XXX_TRIGGER_STOP are triggered.
# When any LOG_XXX_TRIGGER_STOP and any LOG_XXX_TRIGGER_FORCESTOP are triggered at the same time, 'FORCESTOP' would
# be executed.

# Note that LOG_XXX_TRIGGER_STOP and LOG_XXX_TRIGGER_FORCESTOP still would be executed even when current time
# is not within EMAIL_WORKING_DAYS and EMAIL_WORKING_HOURS, though NO email would be sent.
LOG_CRITICAL_THRESHOLD = 0
LOG_CRITICAL_TRIGGER_STOP = False
LOG_CRITICAL_TRIGGER_FORCESTOP = False

LOG_ERROR_THRESHOLD = 0
LOG_ERROR_TRIGGER_STOP = False
LOG_ERROR_TRIGGER_FORCESTOP = False

LOG_WARNING_THRESHOLD = 0
LOG_WARNING_TRIGGER_STOP = False
LOG_WARNING_TRIGGER_FORCESTOP = False

LOG_REDIRECT_THRESHOLD = 0
LOG_REDIRECT_TRIGGER_STOP = False
LOG_REDIRECT_TRIGGER_FORCESTOP = False

LOG_RETRY_THRESHOLD = 0
LOG_RETRY_TRIGGER_STOP = False
LOG_RETRY_TRIGGER_FORCESTOP = False

LOG_IGNORE_THRESHOLD = 0
LOG_IGNORE_TRIGGER_STOP = False
LOG_IGNORE_TRIGGER_FORCESTOP = False


############################## System ##################################
# Set True to enable debug mode and debugger would be available in the browser.
# Actually, it's not recommended to turn on debug mode, also no need,
# since its side effects includes creating two caching subprocess in the background.
DEBUG = False

# Set True to set logging level to DEBUG for getting more information about how ScrapydWeb works
VERBOSE = False
