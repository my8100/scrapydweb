ScrapydWeb: Full-featured web UI for monitoring and controlling Scrapyd servers cluster, with Scrapy log analysis and visualization supported
==========================

Features
---------------

- Multinode Scrapyd Servers
  - Group, filter and select any numbers of nodes
  - Execute command on multinodes with one click

- Scrapy Log Analysis
  - Stats collection
  - Progress visualization
  - Logs categorization

- All Scrapyd API Supported
  - Deploy project, Run Spider, Stop job
  - List projects/versions/spiders/running_jobs
  - Delete version/project

- Others
  - Basic auth for web UI


Maintainer
---------------
- [my8100](https://github.com/my8100)
- [simplety](https://github.com/simplety) (Front-End)


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
then you can custom config with it.

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
  - Stats collection
![log_stats](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/log_stats.png)

  - Progress visualization
![log_chart](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/log_chart.png)

  - Logs categorization
![log_extracted](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/log_extracted.png)

- Deploy Project
![deploy](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/deploy.png)

- Run Spider
![run](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/run.png)

- Manage Projects
![manage](https://raw.githubusercontent.com/my8100/scrapydweb/master/screenshot/manage.png)
