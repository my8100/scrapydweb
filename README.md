ScrapydWeb: Full-featured web UI for monitoring and controlling Scrapyd servers
==========================

Feature Support
---------------

- Multinode Scrapyd Servers
  - Group, filter and select any numbers of nodes
  - Execute command on multinodes with one click

- Scrapy Log Analysis
  - Collect statistics
  - Show crawling progress with chart
  - Extract key logs

- All Scrapyd API supported
  - Deploy project, Run Spider, Stop job
  - List projects/versions/spiders/running_jobs
  - Delete version/project


Maintainer
---------------
- [my8100](https://github.com/my8100)
- [simplety](https://github.com/simplety)(frontend)


Installation
------------

To install ScrapydWeb, simply use pip:

``` {.sourceCode .bash}
$ pip install scrapydweb
```


Start Up
------------

Run "scrapydweb -h" to get help,
and a config file named "scrapydweb_settings.py" would be copied to the working directory,
then you can custom config with it

``` {.sourceCode .bash}
$ scrapydweb
```
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000)


Screenshot
------------

- Overview
![overview](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/overview.png)

- Dashboard
![dashboard](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/dashboard.png)

- Log Analysis
  - Statistics
![log_stats](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/log_stats.png)

  - Crawling progress
![log_chart](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/log_chart.png)

  - Key Logs
![log_extracted](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/log_extracted.png)

- Deploy Project
![deploy](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/deploy.png)

- Run Spider
![run](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/run.png)

- Manage Projects
![manage](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/manage.png)
