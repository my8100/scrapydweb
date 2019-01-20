# coding: utf8
from tests.utils import req


projects = [
    'demo-',
    'demo--macOS',
    'demo--Ubuntu',
    'demo--Win10cp936',
    'demo--Win7CN',
    'demo--Win7CNsendzipped',
    'demo-Win10cp1252',
    'demo-Win7CNsendzipped',
    'demo_inner',
    'demo_only_scrapy_cfg',
    'demo_outer',
    'demo_unicode',
    'fakeproject',
    'ScrapydWeb_demo',
    'scrapy_cfg_no_deploy_project',
    'scrapy_cfg_no_option_project',
    'scrapy_cfg_no_option_project_value',
    'scrapy_cfg_no_section_deploy'
]


def test_cleantest(app, client):
    for project in projects:
        req(app, client, view='api', kws=dict(node=1, opt='delproject', project=project))
