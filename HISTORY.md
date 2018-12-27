Release History
===============
1.0.0 (2018-12-27)
------------------
- Formal release of v1.0.0 :tada: :cake: :tada:
- Bugs fixed
  - Remove inject_variable() in the base view class **to avoid memory leak** [(issue #14)](https://github.com/my8100/scrapydweb/issues/14)
  - Parse project name from scrapy.cfg instead of setting it to the folder name for auto eggifying [(issue #15)](https://github.com/my8100/scrapydweb/issues/15)
  - Fix the 'CheckAll / UncheckAll' checkbox and the 'Upload file' javascript in Safari
  - Fix the 'go-top' and 'go-bottom' buttons in Firefox
  - Fix faulty links in dropdown menu in the cached Log and Stats page of mobile UI
- Introduce new UI for the Deploy page
- Add 500.html for 'Internal Server Error'
- Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v6.py'


1.0.0rc2 (2018-12-10)
------------------
- Fix the faulty auth for the first selected node when deploying project or scheduling spider
- Add :iphone: **Mobile UI** (only support the Dashboard, Log, and Stats page)
- Add test codes for Scrapyd cluster
- Remove the url_for method in all HTML templates
- UI & UX improvements
  - Add clickable drop-down menu (for switching node) for mobile devices
  - Add form validation and remove alert boxes in the Run page
  - Remove confirmation boxes for multinode operations
- Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v5.py'


1.0.0rc1 (2018-11-12)
------------------
- Add :e-mail: **Email Notice**
- Add switch for skipping unselected nodes when using navigation buttons
- **Refactor codes**
- Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v4.py'


0.9.9 (2018-10-24)
------------------
- Fix the bug that **fails to start up on macOS** because of setting preexec_fn for caching subprocess in v0.9.8
- Add :package: **'Auto eggifying'** and 'Upload egg or compressed file' in the Deploy page
- Add the Settings page
- Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v3.py'


0.9.8 (2018-10-19)
------------------
- Add the mechanism of killing HTML caching subprocess when the main process is killed


0.9.7 (2018-10-16)
------------------
- Fix the bug that fails to read lastModifiedDate of egg file in Firefox and Safari


0.9.6 (2018-10-15)
------------------
- Support accessing Scrapyd servers protected by basic auth
- Update caching mechanism: finished job would be cached only once
- Add navigation buttons for switching to the same page (e.g. the Stats page) of a neighboring node
- Remove .log.gz and .gz extension in the 'Parse log' page
- Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v2.py'


0.9.5 (2018-10-12)
------------------
- Fix the bug that auth argument from the command line does not take effect
- Add the Items page
- Add SCRAPYD_LOG_EXTENSIONS for locating Scrapy log


0.9.4 (2018-10-10)
------------------
- Add :closed_lock_with_key: **basic auth for web UI**


0.9.3 (2018-10-08)
------------------
- Add __version__.py and update setup.py


0.9.2 (2018-10-01)
------------------
- Update README.md and screenshot


0.9.1 (2018-09-30)
------------------
- First release version
