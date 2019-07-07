:abc: English | [:mahjong: 简体中文](https://github.com/my8100/scrapydweb/blob/master/README_CN.md)

# ScrapydWeb: Web app for Scrapyd cluster management, with support for Scrapy log analysis & visualization.

[![PyPI - scrapydweb Version](https://img.shields.io/pypi/v/scrapydweb.svg)](https://pypi.org/project/scrapydweb/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/scrapydweb.svg)](https://pypi.org/project/scrapydweb/)
[![CircleCI](https://circleci.com/gh/my8100/scrapydweb/tree/master.svg?style=shield)](https://circleci.com/gh/my8100/scrapydweb/tree/master)
[![codecov](https://codecov.io/gh/my8100/scrapydweb/branch/master/graph/badge.svg)](https://codecov.io/gh/my8100/scrapydweb)
[![Coverage Status](https://coveralls.io/repos/github/my8100/scrapydweb/badge.svg?branch=master)](https://coveralls.io/github/my8100/scrapydweb?branch=master)
[![Downloads - total](https://pepy.tech/badge/scrapydweb)](https://pepy.tech/project/scrapydweb)
[![GitHub license](https://img.shields.io/github/license/my8100/scrapydweb.svg)](https://github.com/my8100/scrapydweb/blob/master/LICENSE)
[![Twitter](https://img.shields.io/twitter/url/https/github.com/my8100/scrapydweb.svg?style=social)](https://twitter.com/intent/tweet?text=@my8100_%20ScrapydWeb:%20Web%20app%20for%20Scrapyd%20cluster%20management,%20with%20support%20for%20Scrapy%20log%20analysis%20%26%20visualization.%20%23python%20%23scrapy%20%23scrapyd%20%23webscraping%20%23scrapydweb%20&url=https%3A%2F%2Fgithub.com%2Fmy8100%2Fscrapydweb)


##
![servers](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshots/servers.png)

## Scrapyd :x: ScrapydWeb :x: LogParser
### :book: Recommended Reading
[:link: How to efficiently manage your distributed web scraping projects](https://github.com/my8100/files/blob/master/scrapydweb/README.md)

[:link: How to set up Scrapyd cluster on Heroku](https://github.com/my8100/scrapyd-cluster-on-heroku)


## :eyes: Demo
[:link: scrapydweb.herokuapp.com](https://scrapydweb.herokuapp.com)


## :star: Features
<details>
<summary>View contents</summary>

- :diamond_shape_with_a_dot_inside: Scrapyd Cluster Management
  - :100: All Scrapyd JSON API Supported
  - :ballot_box_with_check: Group, filter and select any number of nodes
  - :computer_mouse: **Execute command on multinodes with just a few clicks**

- :mag: Scrapy Log Analysis
  - :bar_chart: Stats collection
  - :chart_with_upwards_trend: **Progress visualization**
  - :bookmark_tabs: Logs categorization

- :battery: Enhancements
  - :package: **Auto packaging**
  - :male_detective: **Integrated with [:link: *LogParser*](https://github.com/my8100/logparser)**
  - :alarm_clock: **Timer tasks**
  - :e-mail: **Email notice**
  - :iphone: Mobile UI
  - :closed_lock_with_key: Basic auth for web UI

</details>


## :computer: Getting Started
<details>
<summary>View contents</summary>

### :warning: Prerequisites
:heavy_exclamation_mark: **Make sure that [:link: Scrapyd](https://github.com/scrapy/scrapyd) has been installed and started on all of your hosts.**

:bangbang: Note that for remote access, you have to manually set 'bind_address = 0.0.0.0' in [:link: the configuration file of Scrapyd](https://scrapyd.readthedocs.io/en/latest/config.html#example-configuration-file)
and restart Scrapyd to make it visible externally.

### :arrow_down: Install
- Use pip:
```bash
pip install scrapydweb
```
:heavy_exclamation_mark: Note that you may need to execute `pip install -U pip` first in order to get the latest version of scrapydweb, or download the tar.gz file from https://pypi.org/project/scrapydweb/#files and get it installed via `pip install scrapydweb-x.x.x.tar.gz`

- Use git:
```bash
git clone https://github.com/my8100/scrapydweb.git
cd scrapydweb
python setup.py install
```

### :arrow_forward: Start
1. Start ScrapydWeb via command `scrapydweb`. (a config file would be generated for customizing settings at the first startup.)
2. Visit http://127.0.0.1:5000 **(It's recommended to use Google Chrome for a better experience.)**

### :globe_with_meridians: Browser Support
The latest version of Google Chrome, Firefox, and Safari.

</details>


## :heavy_check_mark: Running the tests
<details>
<summary>View contents</summary>

<br>

```bash
$ git clone https://github.com/my8100/scrapydweb.git
$ cd scrapydweb

# To create isolated Python environments
$ pip install virtualenv
$ virtualenv venv/scrapydweb
# Or specify your Python interpreter: $ virtualenv -p /usr/local/bin/python3.7 venv/scrapydweb
$ source venv/scrapydweb/bin/activate

# Install dependent libraries
(scrapydweb) $ python setup.py install
(scrapydweb) $ pip install pytest
(scrapydweb) $ pip install coverage

# Make sure Scrapyd has been installed and started, then update the custom_settings item in tests/conftest.py
(scrapydweb) $ vi tests/conftest.py
(scrapydweb) $ curl http://127.0.0.1:6800

# '-x': stop on first failure
(scrapydweb) $ coverage run --source=scrapydweb -m pytest tests/test_a_factory.py -s -vv -x
(scrapydweb) $ coverage run --source=scrapydweb -m pytest tests -s -vv --disable-warnings
(scrapydweb) $ coverage report
# To create an HTML report, check out htmlcov/index.html
(scrapydweb) $ coverage html
```

</details>


## :building_construction: Built With
<details>
<summary>View contents</summary>

<br>

- Front End
  - [:link: Element](https://github.com/ElemeFE/element)
  - [:link: ECharts](https://github.com/apache/incubator-echarts)

- Back End
  - [:link: Flask](https://github.com/pallets/flask)

</details>


## :clipboard: Changelog
Detailed changes for each release are documented in the [:link: HISTORY.md](https://github.com/my8100/scrapydweb/blob/master/HISTORY.md).


## :man_technologist: Author
| [<img src="https://github.com/my8100.png" width="100px;"/>](https://github.com/my8100)<br/> [<sub>my8100</sub>](https://github.com/my8100) |
| --- |


## :busts_in_silhouette: Contributors
| [<img src="https://github.com/simplety.png" width="100px;"/>](https://github.com/simplety)<br/> [<sub>Kaisla</sub>](https://github.com/simplety) |
| --- |


## :copyright: License
This project is licensed under the GNU General Public License v3.0 - see the [:link: LICENSE](https://github.com/my8100/scrapydweb/blob/master/LICENSE) file for details.
