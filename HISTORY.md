Release History
===============
1.0.0rc2 (2018-12-10)
------------------
- Fix the bug that mistakenly sets the auth for the first selected node when deploying project or scheduling spider
- Add **Mobile UI** (Dashboard page only)
- Add test codes for Scrapyd cluster
- Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v5.py'


1.0.0rc1 (2018-11-12)
------------------
- Add **Email Notice**
- Add switch for skipping unselected nodes when using navigation buttons
- **Refactor codes**
- Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v4.py'


0.9.9 (2018-10-24)
------------------
- Fix the bug that **fails to start up on macOS** because of setting preexec_fn for caching subprocess in v0.9.8
- Add **'Auto eggifying'** and 'Upload egg or compressed file' in Deploy page
- Add Settings page
- Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v3.py'


0.9.8 (2018-10-19)
------------------
- Add the mechanism of killing HTML caching subprocess when main process is killed


0.9.7 (2018-10-16)
------------------
- Fix the bug that fails to read lastModifiedDate of egg file in Firefox and Safari


0.9.6 (2018-10-15)
------------------
- Support accessing Scrapyd servers protected by basic auth
- Update caching mechanism: finished job would be cached only once
- Add navigation buttons for switching to same page (like 'Stats') of neighboring node
- Remove .log.gz and .gz extension in 'Parse log' page
- Change SCRAPYDWEB_SETTINGS_PY to 'scrapydweb_settings_v2.py'


0.9.5 (2018-10-12)
------------------
- Fix the bug that auth argument from command line doesnot take effect
- Add Items page
- Add SCRAPYD_LOG_EXTENSIONS for locating Scrapy log


0.9.4 (2018-10-10)
------------------
- Support basic auth for web UI


0.9.3 (2018-10-08)
------------------
- Add __version__.py and update setup.py


0.9.2 (2018-10-01)
------------------
- Update README.md and screenshot


0.9.1 (2018-09-30)
------------------
- First release version
