Release History
===============
1.2.0 (2019-03-12)
------------------
- New Features
  - Support :alarm_clock: **Timer Tasks** to schedule a spider run periodically [(issue #4)](https://github.com/my8100/scrapydweb/issues/4)
  - Persist jobs information in database [(issue #21)](https://github.com/my8100/scrapydweb/issues/21)
- Improvements
  - Adapt to [:link: *LogParser*](https://github.com/my8100/logparser) v0.8.1, show Crawler.stats and Crawler.engine
    in the Stats page if available.
  - Support backing up stats json files in case the original logfiles are deleted by Scrapyd
  - Support setting up EMAIL_USERNAME separately [(issue #28)](https://github.com/my8100/scrapydweb/issues/28)
  - Introduce new UI for the Jobs, Logs, and Items page
  - Add 'Sync from Servers page' checkbox in the Deploy Project and Run Spider page
  - Rename 'Overview' to 'Servers', 'Dashboard' to 'Jobs'
- Others
  - Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v8.py'


1.1.0 (2019-01-20)
------------------
- New Features
  - **Integrated with [:link: *LogParser*](https://github.com/my8100/logparser)**
- Improvements
  - Remove **HTML caching**
  - Add 'List Stats' in the Overview page
  - Show crawled_pages and scraped_items in the Dashboard page
- Bug Fixes
  - Integrated with LogParser to avoid MemoryError when parsing large logfiles [(issue #11)](https://github.com/my8100/scrapydweb/issues/11)
  - Support running ScrapydWeb in HTTPS mode [(issue #18)](https://github.com/my8100/scrapydweb/issues/18)
- Others
  - Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v7.py'


1.0.0 (2018-12-27)
------------------
- Formal release of v1.0.0 :tada: :cake: :beer:
- Improvements
  - Introduce new UI for the Deploy Project page
  - Add 500.html for 'Internal Server Error'
- Bug Fixes
  - Remove inject_variable() in the base view class **to avoid memory leak** [(issue #14)](https://github.com/my8100/scrapydweb/issues/14)
  - Parse project name from scrapy.cfg instead of setting it to the folder name for auto packaging [(issue #15)](https://github.com/my8100/scrapydweb/issues/15)
  - Fix the 'CheckAll / UncheckAll' checkbox and the 'Upload file' function in Safari
  - Fix the 'go-top' and 'go-bottom' buttons in Firefox
  - Fix faulty links in dropdown menu in the cached Log and Stats page of mobile UI
- Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v6.py'


1.0.0rc2 (2018-12-10)
------------------
- New Features
  - Add :iphone: **Mobile UI** (only support the Dashboard, Log, and Stats page)
- Improvements
  - Add clickable drop-down menu (for switching node) for mobile devices
  - Add form validation and remove alert boxes in the Run Spider page
  - Remove confirmation boxes for multinode operations
- Bug Fixes
  - Fix the faulty auth for the first selected node when deploying project or scheduling spider
- Others
  - Add test codes for Scrapyd cluster
  - Remove the url_for method from all HTML templates
  - Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v5.py'


1.0.0rc1 (2018-11-12)
------------------
- New Features
  - Add :e-mail: **Email Notice**
- Improvements
  - Add switch for skipping unselected nodes when using navigation buttons
- Others
  - **Refactor codes**
  - Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v4.py'


0.9.9 (2018-10-24)
------------------
- New Features
  - Support :package: **Auto packaging** and 'Upload egg or compressed file' in the Deploy Project page
- Improvements
  - Add the Settings page
- Bug Fixes
  - Fix the bug that **fails to start up on macOS** because of setting preexec_fn for caching subprocess in v0.9.8
- Others
  - Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v3.py'


0.9.8 (2018-10-19)
------------------
- Others
  - Add the mechanism of killing HTML caching subprocess when the main process is killed


0.9.7 (2018-10-16)
------------------
- Bug Fixes
  - Fix the bug that fails to read lastModifiedDate of egg file in Firefox and Safari


0.9.6 (2018-10-15)
------------------
- Improvements
  - Support accessing Scrapyd servers protected by basic auth
  - Add navigation buttons for switching to the same page (e.g. the Stats page) of a neighboring node
  - Update caching mechanism: finished job would be cached only once
  - Remove .log.gz and .gz extension in the 'Log Parser' page
- Others
  - Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v2.py'


0.9.5 (2018-10-12)
------------------
- Improvements
  - Add the Items page
  - Add SCRAPYD_LOG_EXTENSIONS for locating Scrapy log
- Bug Fixes
  - Fix the bug that auth argument from the command line does not take effect


0.9.4 (2018-10-10)
------------------
- Improvements
  - Support :closed_lock_with_key: **basic auth for web UI**


0.9.3 (2018-10-08)
------------------
- Others
  - Add __version__.py and update setup.py


0.9.2 (2018-10-01)
------------------
- Others
  - Update README.md and screenshots


0.9.1 (2018-09-30)
------------------
- First release version
