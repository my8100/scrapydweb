
def test_monitoring_page_title(page):
    page.goto("/1/monitor/but_fr_pagelist/")
    content = page.text_content("h1")
    assert "Monitoring view for the spider".casefold() in content.casefold()

def test_monitoring_html_codes(page):
    page.goto("/1/monitor/but_fr_pagelist/")
    def check_status(response):
        assert response.status < 400

    page.on("response", check_status)

