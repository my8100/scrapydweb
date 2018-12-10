English | [简体中文](https://github.com/my8100/scrapydweb/blob/master/README_CN.md)

# ScrapydWeb: A full-featured web UI for Scrapyd cluster management, with Scrapy log analysis & visualization supported.

[![PyPI - scrapydweb Version](https://img.shields.io/pypi/v/scrapydweb.svg)](https://pypi.org/project/scrapydweb/)
[![Downloads - total](https://pepy.tech/badge/scrapydweb)](https://pepy.tech/project/scrapydweb)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/scrapydweb.svg)](https://pypi.org/project/scrapydweb/)
[![Coverage Status](https://coveralls.io/repos/github/my8100/scrapydweb/badge.svg?branch=master)](https://coveralls.io/github/my8100/scrapydweb?branch=master)
[![GitHub license](https://img.shields.io/github/license/my8100/scrapydweb.svg)](https://github.com/my8100/scrapydweb/blob/master/LICENSE)
[![Twitter](https://img.shields.io/twitter/url/https/github.com/my8100/scrapydweb.svg?style=social)](https://twitter.com/intent/tweet?text=@my8100_%20ScrapydWeb:%20Full-featured%20web%20UI%20for%20Scrapyd%20cluster%20management,%20Scrapy%20log%20analysis%20%26%20visualization%20%23python%20%23scrapy%20%23scrapyd%20%23webscraping%20%23scrapydweb%20&url=https%3A%2F%2Fgithub.com%2Fmy8100%2Fscrapydweb)


## Scrapyd x ScrapydWeb
### Recommended Reading
[How to efficiently manage your distributed web scraping projects](https://medium.com/@my8100/https-medium-com-my8100-how-to-efficiently-manage-your-distributed-web-scraping-projects-55ab13309820)

![overview](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshots/overview.png)


## Features
- Scrapyd Cluster Management
  - Group, filter and select any number of nodes
  - **Execute command on multinodes with just a few clicks**

- Scrapy Log Analysis
  - Stats collection
  - **Progress visualization**
  - Logs categorization

- All Scrapyd JSON API Supported
  - Deploy project, Run Spider, Stop job
  - List projects/versions/spiders/running_jobs
  - Delete version/project

- Enhancements
  - Basic auth for web UI
  - HTML caching for the Log and Stats page
  - **Auto eggify your projects**
  - **Email notice**
  - Mobile UI

## Getting Started
### Prerequisites
**Make sure that [Scrapyd](https://github.com/scrapy/scrapyd) has been installed and started on all of your hosts.**

Note that if you want to visit your Scrapyd server remotely,
you have to manually set the [bind_address](https://scrapyd.readthedocs.io/en/latest/config.html#bind-address)
 to `bind_address = 0.0.0.0` and restart Scrapyd to make it visible externally.

### Installing ScrapydWeb
-  use pip:
```bash
pip install scrapydweb
```

-  use git:
```bash
git clone https://github.com/my8100/scrapydweb.git
cd scrapydweb
python setup.py install
```

### Starting ScrapydWeb
1. Start ScrapydWeb via the `scrapydweb` command.
(Your would be asked to add your SCRAPYD_SERVERS in the generated config file on first startup.)
2. Visit [http://127.0.0.1:5000](http://127.0.0.1:5000).
**(It's recommended to use Google Chrome to get the best experience.)**

### Browser Support
The latest version of Google Chrome, Firefox and Safari.


## Preview
- [Screenshots](https://github.com/my8100/files/tree/master/scrapydweb/README.md)

- [Gif Demo](https://github.com/my8100/files/tree/master/scrapydweb/README_GIF.md)


## Running the tests
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

(scrapydweb) $ coverage run --source=scrapydweb -m pytest tests/test_a_factory.py -s -vv
(scrapydweb) $ coverage run --source=scrapydweb -m pytest tests -s -vv
(scrapydweb) $ coverage report
# To create an HTML report, check out htmlcov/index.html
(scrapydweb) $ coverage html
```


## Built With
- Back End
  - [Flask](https://github.com/pallets/flask)
  - [Flask-Compress](https://pypi.org/project/Flask-Compress/)
  - [Requests](https://github.com/requests/requests)
- Front End
  - [jQuery](https://github.com/jquery/jquery)
  - [Vue.js](https://github.com/vuejs/vue)
  - [Element](https://github.com/ElemeFE/element)
  - [ECharts](https://github.com/apache/incubator-echarts)


## Changelog
Detailed changes for each release are documented in the [HISTORY.md](./HISTORY.md).


## Author
- [my8100](https://github.com/my8100)


## Contributors
- [simplety](https://github.com/simplety)


## License
This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](./LICENSE) file for details.
