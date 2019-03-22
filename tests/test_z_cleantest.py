# coding: utf-8
from tests.utils import req


projects = [
    'demo_inner',
    'demo_only_scrapy_cfg',
    'demo_outer',
    'demo_unicode',
    'demo___Win10cp1252',
    'demo___Win7CNsendzipped',
    'demo_____',
    'demo________macOS',
    'demo________Ubuntu',
    'demo________Win10cp936',
    'demo________Win7CN',
    'demo________Win7CNsendzipped',
    'fakeproject',
    'ScrapydWeb_demo',
    'scrapy_cfg_no_deploy_project',
    'scrapy_cfg_no_option_project',
    'scrapy_cfg_no_option_project_value',
    'scrapy_cfg_no_section_deploy'
]


def test_cleantest(app, client):
    req(app, client, view='api', kws=dict(node=1, opt='listprojects'))

    for project in projects:
        __, js = req(app, client, view='api', kws=dict(node=1, opt='listjobs', project=project))
        for job in js.get('running', []):
            req(app, client, view='api',
                kws=dict(node=1, opt='forcestop', project=project, version_spider_job=job['id']))
        req(app, client, view='api', kws=dict(node=1, opt='delproject', project=project))
