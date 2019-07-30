# coding: utf-8
from flask import url_for

from tests.utils import cst, req, switch_scrapyd


# Location: http://127.0.0.1:5000/1/jobs/?ui=mobile
def test_index(app, client):
    with app.test_request_context():
        for __, headers in cst.HEADERS_DICT.items():
            req(app, client, view='index', kws=dict(ui='mobile'), headers=headers,
                location=url_for('jobs', node=1, ui='mobile'))

        for key in ['Chrome', 'iPad']:
            req(app, client, view='index', kws={}, headers=cst.HEADERS_DICT[key],
                location=url_for('servers', node=1))

        for key in ['iPhone', 'Android']:
            req(app, client, view='index', kws={}, headers=cst.HEADERS_DICT[key],
                location=url_for('jobs', node=1, ui='mobile'))


def test_check_browser(app, client):
    req(app, client, view='servers', kws=dict(node=2), headers=cst.HEADERS_DICT['IE'], ins='checkBrowser();')
    req(app, client, view='servers', kws=dict(node=2), headers=cst.HEADERS_DICT['EDGE'], ins='checkBrowser();')


def test_dropdown_for_mobile_device(app, client):
    req(app, client, view='servers', kws=dict(node=2), headers=cst.HEADERS_DICT['Chrome'],
        ins='dropdown.css', nos=['dropdown_mobileui.css', 'handleDropdown();'])
    req(app, client, view='servers', kws=dict(node=2), headers=cst.HEADERS_DICT['iPhone'],
        nos='dropdown.css', ins=['dropdown_mobileui.css', 'handleDropdown();'])
    req(app, client, view='servers', kws=dict(node=2), headers=cst.HEADERS_DICT['iPad'],
        nos='dropdown.css', ins=['dropdown_mobileui.css', 'handleDropdown();'])


def test_check_update(app, client):
    @app.context_processor
    def inject_variable():
        return dict(CHECK_LATEST_VERSION_FREQ=1)

    req(app, client, view='servers', kws=dict(node=2),
        ins='<script>setTimeout("checkLatestVersion(', nos='<!-- <script>setTimeout("checkLatestVersion(')

    @app.context_processor
    def inject_variable():
        return dict(CHECK_LATEST_VERSION_FREQ=100)

    req(app, client, view='servers', kws=dict(node=2), nos='<script>setTimeout("checkLatestVersion(')


def test_page(app, client):
    for view, title in cst.VIEW_TITLE_MAP.items():
        req(app, client, view=view, kws=dict(node=1), ins=title)

    req(app, client, view='jobs', kws=dict(node=2), ins='status_code: -1')
    req(app, client, view='items', kws=dict(node=2), ins='status_code: -1')
    req(app, client, view='logs', kws=dict(node=2), ins='status_code: -1')

    switch_scrapyd(app)

    for view, title in cst.VIEW_TITLE_MAP.items():
        req(app, client, view=view, kws=dict(node=2), ins=title)


def test_select_multinode_checkbox(app, client):
    for view in ['deploy', 'schedule']:
        req(app, client, view=view, kws=dict(node=2), ins='CheckAll / UncheckAll')


def test_items(app, client):
    try:
        req(app, client, view='items', kws=dict(node=1), ins='Directory listing for /items/')
    except AssertionError:
        req(app, client, view='items', kws=dict(node=1), ins='No Such Resource')


def test_switch_node_skip(app, client):
    req(app, client, view='servers', kws=dict(node=1),
        ins=['1 / 2', 'onclick="switchNode(1);', 'id="skip_nodes_checkbox"'])
    req(app, client, view='servers', kws=dict(node=2),
        ins=['2 / 2', 'onclick="switchNode(-1);', 'id="skip_nodes_checkbox"'])


# <span>Cluster Reports</span>
# <el-tab-pane label="Get Reports" name="getreports">
def test_cluster_reports_exists(app, client):
    ins = ['<span>Cluster Reports</span>', '<el-tab-pane label="Get Reports"']
    req(app, client, view='servers', kws=dict(node=1), ins=ins)
