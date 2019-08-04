[:abc: English](./README.md) | :mahjong: 简体中文

# ScrapydWeb：用于 Scrapyd 集群管理的 web 应用，支持 Scrapy 日志分析和可视化。

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
### :book: 推荐阅读
[:link: 如何简单高效地部署和监控分布式爬虫项目](https://github.com/my8100/files/blob/master/scrapydweb/README_CN.md)

[:link: 如何免费创建云端爬虫集群](https://github.com/my8100/scrapyd-cluster-on-heroku/blob/master/README_CN.md)


## :eyes: 在线体验
[:link: scrapydweb.herokuapp.com](https://scrapydweb.herokuapp.com)


## :star: 功能特性
<details>
<summary>查看内容</summary>

- :diamond_shape_with_a_dot_inside: Scrapyd 集群管理
  - :100: 支持所有 Scrapyd JSON API
  - :ballot_box_with_check: 支持通过分组和过滤来选择若干个节点
  - :computer_mouse: **一次操作, 批量执行**

- :mag: Scrapy 日志分析
  - :1234: 数据统计
  - :chart_with_upwards_trend: **进度可视化**
  - :bookmark_tabs: 日志分类

- :battery: 增强功能
  - :package: **自动打包项目**
  - :male_detective: **集成 [:link: *LogParser*](https://github.com/my8100/logparser)**
  - :alarm_clock: **定时器任务**
  - :e-mail: **邮件通知**
  - :iphone: 移动端 UI
  - :closed_lock_with_key: web UI 支持基本身份认证

</details>


## :computer: 上手
<details>
<summary>查看内容</summary>

### :warning: 环境要求
:heavy_exclamation_mark: **请先确保所有主机都已经安装和启动 [:link: Scrapyd](https://github.com/scrapy/scrapyd) 。**

:bangbang: 如果需要远程访问 Scrapyd，则需在 [:link: Scrapyd 配置文件](https://scrapyd.readthedocs.io/en/latest/config.html#example-configuration-file)
中设置 'bind_address = 0.0.0.0'，然后重启 Scrapyd。

### :arrow_down: 安装
- 通过 pip:
```bash
pip install scrapydweb
```
:heavy_exclamation_mark: 如果 pip 安装结果不是最新版本的 scrapydweb，请先执行`python -m pip install --upgrade pip`，或者前往 https://pypi.org/project/scrapydweb/#files 下载 tar.gz 文件并执行安装命令 `pip install scrapydweb-x.x.x.tar.gz`

- 通过 git:
```bash
pip install --upgrade git+https://github.com/my8100/scrapydweb.git
```
或:
```bash
git clone https://github.com/my8100/scrapydweb.git
cd scrapydweb
python setup.py install
```

### :arrow_forward: 启动
1. 通过运行命令 `scrapydweb` 启动 ScrapydWeb（首次启动将自动生成配置文件）。
2. 访问 http://127.0.0.1:5000 **（建议使用 Google Chrome 以获取更好体验）**。

### :globe_with_meridians: 浏览器支持
最新版本的 Google Chrome，Firefox 和 Safari。

</details>


## :heavy_check_mark: 执行测试
<details>
<summary>查看内容</summary>

<br>

```bash
$ git clone https://github.com/my8100/scrapydweb.git
$ cd scrapydweb

# 创建虚拟环境
$ pip install virtualenv
$ virtualenv venv/scrapydweb
# 亦可指定 Python 解释器：$ virtualenv -p /usr/local/bin/python3.7 venv/scrapydweb
$ source venv/scrapydweb/bin/activate

# 安装依赖库
(scrapydweb) $ python setup.py install
(scrapydweb) $ pip install pytest
(scrapydweb) $ pip install coverage

# 请先确保已经安装和启动 Scrapyd，然后检查和更新 tests/conftest.py 文件中的 custom_settings
(scrapydweb) $ vi tests/conftest.py
(scrapydweb) $ curl http://127.0.0.1:6800

# '-x': 在第一次出现失败时停止测试
(scrapydweb) $ coverage run --source=scrapydweb -m pytest tests/test_a_factory.py -s -vv -x
(scrapydweb) $ coverage run --source=scrapydweb -m pytest tests -s -vv --disable-warnings
(scrapydweb) $ coverage report
# 生成 HTML 报告, 文件位于 htmlcov/index.html
(scrapydweb) $ coverage html
```

</details>


## :building_construction: 框架和依赖库
<details>
<summary>查看内容</summary>

<br>

- 前端
  - [:link: Element](https://github.com/ElemeFE/element)
  - [:link: ECharts](https://github.com/apache/incubator-echarts)
- 后端
  - [:link: Flask](https://github.com/pallets/flask)

</details>


## :clipboard: 更新日志
详见 [:link: HISTORY.md](./HISTORY.md)。


## :man_technologist: 作者
| [<img src="https://github.com/my8100.png" width="100px;"/>](https://github.com/my8100)<br/> [<sub>my8100</sub>](https://github.com/my8100) |
| --- |


## :busts_in_silhouette: 贡献者
| [<img src="https://github.com/simplety.png" width="100px;"/>](https://github.com/simplety)<br/> [<sub>Kaisla</sub>](https://github.com/simplety) |
| --- |


## :copyright: 软件许可
本项目采用 GNU General Public License v3.0 许可协议，详见 [:link: LICENSE](./LICENSE)。
