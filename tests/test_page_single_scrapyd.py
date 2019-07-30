# coding: utf-8
from flask import url_for

from tests.utils import cst, req_single_scrapyd


# Location: http://127.0.0.1:5000/1/jobs/?ui=mobile
def test_index(app, client):
    with app.test_request_context():
        for __, headers in cst.HEADERS_DICT.items():
            req_single_scrapyd(app, client, view='index', kws=dict(ui='mobile'), headers=headers,
                               location=url_for('jobs', node=1, ui='mobile'))

        for key in ['Chrome', 'iPad']:
            req_single_scrapyd(app, client, view='index', kws={}, headers=cst.HEADERS_DICT[key],
                               location=url_for('jobs', node=1))  # not the Servers page

        for key in ['iPhone', 'Android']:
            req_single_scrapyd(app, client, view='index', kws={}, headers=cst.HEADERS_DICT[key],
                               location=url_for('jobs', node=1, ui='mobile'))


def test_check_browser(app, client):
    ins = 'checkBrowser();'
    req_single_scrapyd(app, client, view='jobs', kws=dict(node=1), headers=cst.HEADERS_DICT['IE'], ins=ins)
    req_single_scrapyd(app, client, view='jobs', kws=dict(node=1), headers=cst.HEADERS_DICT['EDGE'], ins=ins)


def test_dropdown_for_mobile_device(app, client):
    req_single_scrapyd(app, client, view='jobs', kws=dict(node=1), headers=cst.HEADERS_DICT['Chrome'],
                       ins='dropdown.css', nos=['dropdown_mobileui.css', 'handleDropdown();'])
    req_single_scrapyd(app, client, view='jobs', kws=dict(node=1), headers=cst.HEADERS_DICT['iPhone'],
                       nos='dropdown.css', ins=['dropdown_mobileui.css', 'handleDropdown();'])
    req_single_scrapyd(app, client, view='jobs', kws=dict(node=1), headers=cst.HEADERS_DICT['iPad'],
                       nos='dropdown.css', ins=['dropdown_mobileui.css', 'handleDropdown();'])


def test_check_update(app, client):
    @app.context_processor
    def inject_variable():
        return dict(CHECK_LATEST_VERSION_FREQ=1)

    req_single_scrapyd(app, client, view='jobs', kws=dict(node=1),
                       ins='<script>setTimeout("checkLatestVersion(',
                       nos='<!-- <script>setTimeout("checkLatestVersion(')

    req_single_scrapyd(app, client, view='jobs', kws=dict(node=1, ui='mobile'), mobileui=True,
                       ins='<script>setTimeout("checkLatestVersion(',
                       nos='<!-- <script>setTimeout("checkLatestVersion(')

    @app.context_processor
    def inject_variable():
        return dict(CHECK_LATEST_VERSION_FREQ=100)

    req_single_scrapyd(app, client, view='jobs', kws=dict(node=1), nos='<script>setTimeout("checkLatestVersion(')
    req_single_scrapyd(app, client, view='jobs', kws=dict(node=1, ui='mobile'), mobileui=True,
                       nos='<script>setTimeout("checkLatestVersion(')


def test_page(app, client):
    for view, title in cst.VIEW_TITLE_MAP.items():
        req_single_scrapyd(app, client, view=view, kws=dict(node=1), ins=title)


def test_select_multinode_checkbox(app, client):
    for view in ['deploy', 'schedule']:
        req_single_scrapyd(app, client, view=view, kws=dict(node=1), nos='CheckAll / UncheckAll')


def test_items(app, client):
    try:
        req_single_scrapyd(app, client, view='items', kws=dict(node=1), ins='Directory listing for /items/')
    except AssertionError:
        req_single_scrapyd(app, client, view='items', kws=dict(node=1), ins='No Such Resource')


def test_switch_node_skip(app, client):
    req_single_scrapyd(app, client, view='jobs', kws=dict(node=1),
                       nos=['onclick="switchNode', 'id="skip_nodes_checkbox"'])


# <span>Cluster Reports</span>
# <el-tab-pane label="Get Reports" name="getreports">
def test_cluster_reports_not_exists(app, client):
    nos = ['<span>Cluster Reports</span>', '<el-tab-pane label="Get Reports"']
    req_single_scrapyd(app, client, view='servers', kws=dict(node=1), nos=nos)
