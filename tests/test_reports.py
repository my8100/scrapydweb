# coding: utf-8
from flask import url_for

from tests.utils import cst, req, req_single_scrapyd


def test_node_reports_pass(app, client):
    with app.test_request_context():
        url_report = url_for('log', node=1, opt='report', project='PROJECT_PLACEHOLDER',
                             spider='SPIDER_PLACEHOLDER', job='JOB_PLACEHOLDER')
    ins = ["url_report: '%s'," % url_report, "start: '", "finish: '"]
    req(app, client, view='nodereports', kws=dict(node=1), ins=ins)
    req_single_scrapyd(app, client, view='nodereports', kws=dict(node=1), ins=ins)


def test_node_reports_fail(app, client):
    ins = ['<title>fail - ScrapydWeb</title>', '<h3>status_code: -1</h3>']
    req(app, client, view='nodereports', kws=dict(node=2), ins=ins)
    req_single_scrapyd(app, client, view='nodereports', kws=dict(node=1), ins=ins, set_to_second=True)


def test_cluster_reports(app, client):
    with app.test_request_context():
        url_servers = url_for('servers', node=2, opt='getreports', project=cst.PROJECT,
                              spider=cst.SPIDER, version_job=cst.JOBID)
        url_jobs = url_for('jobs', node=1)
        url_report = url_for('log', node=2, opt='report', project=cst.PROJECT,
                             spider=cst.SPIDER, job=cst.JOBID)
        url_redirect_to_clusterreports = url_for('clusterreports', node=1, project=cst.PROJECT,
                                                 spider=cst.SPIDER, job=cst.JOBID)
    ins = ['0 Reports of ////', '>Select a job</el-button>', url_jobs, 'selected_nodes: [],']
    nos = ['>Select nodes</el-button>']
    req(app, client, view='clusterreports', kws=dict(node=1), ins=ins)

    # Post from the servers page
    data = {
        '1': 'on',
        '2': 'on',
    }
    ins[0] = '%s Reports of /%s/%s/%s/' % (len(data), cst.PROJECT, cst.SPIDER, cst.JOBID)
    ins[-1] = 'selected_nodes: [1, 2],'
    ins.extend(nos)
    ins.append(url_servers)
    ins.append(url_report)
    kws = dict(node=2, project=cst.PROJECT, spider=cst.SPIDER, job=cst.JOBID)
    req(app, client, view='clusterreports', kws=kws, data=data, ins=ins)

    # Load metadata
    ins = ['<h1>Redirecting...</h1>', 'href="%s"' % url_redirect_to_clusterreports]
    req(app, client, view='clusterreports', kws=dict(node=1), ins=ins)
