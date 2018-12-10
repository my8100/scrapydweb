# coding: utf8
from flask import url_for

from tests.utils import VIEW_TITLE_MAP, HEADERS_DICT, get_text, is_mobileui


# Location: http://127.0.0.1:5000/1/dashboard/?ui=mobile
def test_index(client):
    url = '/'
    url_mobileui = '/?ui=mobile'

    for __, headers in HEADERS_DICT.items():
        response = client.get(url_mobileui, headers=headers)
        assert response.headers['Location'].endswith('/1/dashboard/?ui=mobile')

    for key in ['Chrome', 'iPad']:
        response = client.get(url, headers=HEADERS_DICT[key])
        assert response.headers['Location'].endswith('/1/overview/')
    for key in ['iPhone', 'Android']:
        response = client.get(url, headers=HEADERS_DICT[key])
        assert response.headers['Location'].endswith('/1/dashboard/?ui=mobile')


def test_check_browser(app, client):
    with app.test_request_context():
        url = url_for('overview', node=1)
        response = client.get(url, headers=HEADERS_DICT['IE'])
        assert 'checkBrowser()' in get_text(response)

        response = client.get(url, headers=HEADERS_DICT['EDGE'])
        assert 'checkBrowser()' in get_text(response)


def test_dropdown_for_mobile_device(app, client):
    with app.test_request_context():
        url = url_for('overview', node=1)
        response = client.get(url, headers=HEADERS_DICT['Chrome'])
        text = get_text(response)
        assert 'dropdown_mobileui.css' not in text and 'handleDropdown()' not in text

        response = client.get(url, headers=HEADERS_DICT['iPhone'])
        text = get_text(response)
        assert 'dropdown_mobileui.css' in text and 'handleDropdown()' in text

        response = client.get(url, headers=HEADERS_DICT['iPad'])
        text = get_text(response)
        assert 'dropdown_mobileui.css' in text and 'handleDropdown()' in text


def test_check_update(app, client):
    with app.test_request_context():
        @app.context_processor
        def inject_variable():
            return dict(CHECK_LATEST_VERSION_FREQ=1)

        url = url_for('overview', node=1)
        response = client.get(url)
        text = get_text(response)
        assert ('<script>setTimeout("checkLatestVersion(' in text
                and '<!-- <script>setTimeout("checkLatestVersion(' not in text)

        @app.context_processor
        def inject_variable():
            return dict(CHECK_LATEST_VERSION_FREQ=100)
        response = client.get(url)
        text = get_text(response)
        assert '<script>setTimeout("checkLatestVersion(' not in text


def test_page(app, client):
    with app.test_request_context():
        for view, title in VIEW_TITLE_MAP.items():
            url = url_for(view, node=1)
            response = client.get(url)
            assert title in get_text(response) and not is_mobileui(response)

    app.config['SCRAPYD_SERVERS'] = app.config['SCRAPYD_SERVERS'][::-1]
    with app.test_request_context():
        url = url_for('dashboard', node=1)
        response = client.get(url)
        assert 'status_code: -1' in get_text(response)

        for view, title in VIEW_TITLE_MAP.items():
            url = url_for(view, node=2)
            response = client.get(url)
            assert title in get_text(response) and not is_mobileui(response)


def test_select_multinode_checkbox(app, client):
    with app.test_request_context():
        keyword = 'CheckAll / UncheckAll'
        for view in ['deploy.deploy', 'schedule.schedule']:
            url = url_for(view, node=1)
            response = client.get(url)
            assert keyword in get_text(response)


def test_items(app, client):
    title = 'Directory listing for /items/'
    with app.test_request_context():
        url = url_for('items', node=1)
        response = client.get(url)
        assert ((title in get_text(response) or 'No Such Resource' in get_text(response))
                and not is_mobileui(response))


def test_switch_node_skip(app, client):
    with app.test_request_context():
        url = url_for('overview', node=1)
        response = client.get(url)
        assert ('1 / 2' in get_text(response)
                and 'onclick="switchNode' in get_text(response)
                and 'id="skip_nodes_checkbox"' in get_text(response))
