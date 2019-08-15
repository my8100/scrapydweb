# coding: utf-8
import json

from tests.utils import cst, req, sleep


def test_send_text_page(app, client):
    req(app, client, view='sendtext', kws=dict(node=1), ins=['Send text via', 'import scrapy'])


def test_email_pass(app, client):
    if not app.config.get('EMAIL_PASSWORD', ''):
        print("EMAIL_PASSWORD empty")
        return

    def check_pass(recipients=None, subject='Email from #scrapydweb', text=None):
        assert js['status'] == cst.OK
        assert js['result']['reason'] == 'Sent'
        assert js['result']['sender'] == app.config['EMAIL_SENDER']
        if recipients is not None:
            assert js['result']['recipients'] == recipients
        if subject is not None:
            assert js['result']['subject'] == subject
        if text is not None:
            assert js['result']['text'] == text
        assert 'debug' not in js
        assert js['when']
        sleep(5)

    # 'email'
    nos = ['debug', 'email_password']
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='email'), nos=nos)
    check_pass(text='test')

    # 'email/<text>'
    text = 'test email text'
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='email', text=text))
    check_pass(text=text)

    # 'email/<channel_chatid_subject>/<text>'
    text = 'test email subject text'
    channel_chatid_subject = text + ' #scrapydweb'
    kws = dict(opt='email', channel_chatid_subject=channel_chatid_subject, text=text)
    __, js = req(app, client, view='sendtextapi', kws=kws)
    check_pass(text=text, subject=channel_chatid_subject)

    # ?recipients=&subject=
    recipients = app.config['EMAIL_RECIPIENTS'] + ['my8100@gmail.com']
    text = 'test email text recipients and subject in query strings'
    subject = text + ' #scrapydweb'
    kws = dict(opt='email', text=text, recipients=';'.join(recipients), subject=subject)
    __, js = req(app, client, view='sendtextapi', kws=kws)
    check_pass(recipients=recipients, subject=subject, text=text)

    # post form
    recipients = ['my8100@gmail.com'] + app.config['EMAIL_RECIPIENTS']
    value = 'test email post form #scrapydweb'
    subject = value + ' #scrapydweb'
    # Cannot directly pass in a list type to the data, otherwise, only the first recipient could be recognized.
    data = dict(recipients=','.join(recipients), subject=subject, a=1, arg=value, Chinese=u'中文')
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='email'), data=data)
    check_pass(recipients=recipients, subject=subject, text=None)
    data['a'] = str(data['a'])
    assert json.loads(js['result']['text']) == data

    # post json
    # requests.post('http://httpbin.org/post', data=dict(a=1, b=2)).json()
    # {'data': '',
     # 'form': {'a': '1', 'b': '2'},
     # 'headers': {'Content-Type': 'application/x-www-form-urlencoded',},
     # 'json': None,}
    # requests.post('http://httpbin.org/post', json=dict(a=1, b=2)).json()
    # {'data': '{"a": 1, "b": 2}',
     # 'form': {},
     # 'headers': {'Content-Type': 'application/json',},
     # 'json': {'a': 1, 'b': 2},}
    # https://stackoverflow.com/questions/10434599/get-the-data-received-in-a-flask-request
    # request.headers:
    # Content-Type: application/x-www-form-urlencoded
    # Content-Type: application/json
    # https://stackoverflow.com/questions/28836893/how-to-send-requests-with-jsons-in-unit-tests
    recipients = app.config['EMAIL_RECIPIENTS'] + ['my8100@gmail.com']
    value = 'test email post json #scrapydweb'
    subject = value + ' #scrapydweb'
    data = dict(recipients=recipients, subject=subject, b=2, arg=value, Chinese=u'中文')
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='email'),
                 data=json.dumps(data), content_type='application/json')
    check_pass(recipients=recipients, subject=subject, text=None)
    assert json.loads(js['result']['text']) == data


def test_email_fail(app, client):
    # EMAIL_RECIPIENTS invalid
    # "reason": "{'1@2': (501, b'Bad address syntax')}"
    req(app, client, view='sendtextapi', kws=dict(opt='email', recipients='1@2'),
        jskws=dict(status=cst.ERROR), jskeys=['status', 'result', 'debug', 'when'],
        ins='email_password', nos='Sent')

    # EMAIL_PASSWORD unset
    app.config['EMAIL_PASSWORD'] = ''
    req(app, client, view='sendtextapi', kws=dict(opt='email'),
        jskws=dict(status=cst.ERROR, result="The EMAIL_PASSWORD option is unset"))

    # EMAIL_PASSWORD invalid
    # "reason": "Error: 请使用授权码登录。详情请看: http://service.mail.qq.com/cgi-bin/help?subtype=1&&id=28&&no=1001256"
    app.config['EMAIL_PASSWORD'] = 'fake_password'
    req(app, client, view='sendtextapi', kws=dict(opt='email'),
        jskws=dict(status=cst.ERROR), jskeys=['status', 'result', 'debug', 'when'],
        ins='email_password', nos='Sent')


def test_slack_pass(app, client):
    if not app.config['SLACK_TOKEN']:
        print("SLACK_TOKEN unset")
        return

    def check_pass(text=None):
        assert js['url'] == 'https://slack.com/api/chat.postMessage'
        assert js['status_code'] == 200
        assert js['status'] == cst.OK
        assert js['result']['ok'] is True
        if text is not None:
            assert js['result']['message']['text'] == text
        assert 'debug' not in js
        assert js['when']

    # 'slack'
    nos = ['debug', 'token', 'error']
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='slack'), nos=nos)
    check_pass('test')
    channel_general = js['result']['channel']

    # 'slack/<text>'
    text = 'test slack text'
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='slack', text=text))
    check_pass(text)

    # 'slack/<channel_chatid_subject>/<text>'
    channel = 'random'  # general -> "channel": "CLX124N0Z", random -> "channel": "CLRUUNCCT"
    text = 'test slack channel %s and text' % channel
    kws = dict(opt='slack', channel_chatid_subject=channel, text=text)
    __, js = req(app, client, view='sendtextapi', kws=kws)
    check_pass(text)
    channel_random = js['result']['channel']
    assert channel_random != channel_general

    # post form and channel in query string
    channel = 'random'
    value = "slack post form and channel %s in query string" % channel
    data = dict(a=1, arg=value, Chinese=u'中文')
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='slack', channel=channel), data=data)
    check_pass()
    data['a'] = str(data['a'])
    assert json.loads(js['result']['message']['text']) == data
    assert js['result']['channel'] == channel_random

    # post json
    channel = 'random'
    value = "slack post json and channel %s in data" % channel
    data = dict(channel=channel, b=2, arg=value, Chinese=u'中文')
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='slack'),
                 data=json.dumps(data), content_type='application/json')
    check_pass()
    assert json.loads(js['result']['message']['text']) == data
    assert js['result']['channel'] == channel_random


def test_slack_fail(app, client):
    kws = dict(opt='slack')
    jskeys = ['url', 'status_code', 'status', 'result', 'debug', 'when']

    def check_fail(status_code=None, result=None):
        assert js['status'] == 'error'
        assert js['url'] == 'https://slack.com/api/chat.postMessage'
        if status_code is not None:
            assert js['status_code'] == status_code
        if result is not None:
            assert js['result'] == result
        assert js['when']

    # SLACK_TOKEN unset
    token = app.config['SLACK_TOKEN']
    app.config['SLACK_TOKEN'] = ''
    req(app, client, view='sendtextapi', kws=kws,
        jskws=dict(status=cst.ERROR, result="The SLACK_TOKEN option is unset"))

    if not token:
        return
    else:
        app.config['SLACK_TOKEN'] = token

    # SLACK_TOKEN invalid
    fake_token = 'fake_token'
    app.config['SLACK_TOKEN'] = fake_token
    __, js = req(app, client, view='sendtextapi', kws=kws, jskeys=jskeys)
    check_fail(status_code=200, result={'error': 'invalid_auth', 'ok': False})
    assert js['debug'] == {'channel': app.config['SLACK_CHANNEL'], 'text': 'test', 'token': fake_token}

    app.config['SLACK_TOKEN'] = token

    # SLACK_CHANNEL invalid
    fake_channel = 'fake_channel'
    app.config['SLACK_CHANNEL'] = fake_channel
    __, js = req(app, client, view='sendtextapi', kws=kws, jskeys=jskeys)
    check_fail(status_code=200, result={'error': 'channel_not_found', 'ok': False})
    assert js['debug'] == {'channel': fake_channel, 'text': 'test', 'token': app.config['SLACK_TOKEN']}


# On win7, set ENABLE_TELEGRAM_ALERT=True to test Telegram seperately
def test_telegram_pass(app, client):
    if not (app.config['TELEGRAM_TOKEN'] and app.config['ENABLE_TELEGRAM_ALERT']):
        print("ENABLE_TELEGRAM_ALERT False or TELEGRAM_TOKEN unset")
        return

    def check_pass(text=None):
        assert js['url'] == 'https://api.telegram.org/bot%s/sendMessage' % app.config['TELEGRAM_TOKEN']
        assert js['status_code'] == 200
        assert js['status'] == cst.OK
        assert js['result']['ok'] is True
        if text is not None:
            assert js['result']['result']['text'] == text
        assert 'debug' not in js
        assert js['when']

    # 'telegram' | 'tg'
    nos = ['debug', 'token', 'error']
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='telegram'), nos=nos)
    check_pass('test')
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='tg'), nos=nos)
    check_pass('test')

    # 'tg/<text>'
    text = 'test tg text'
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='tg', text=text))
    check_pass(text)

    # 'tg/<channel_chatid_subject>/<text>'
    chat_id = app.config['TELEGRAM_CHAT_ID']
    app.config['TELEGRAM_CHAT_ID'] = 0
    text = 'test tg chat_id text'
    kws = dict(opt='tg', channel_chatid_subject=chat_id, text=text)
    __, js = req(app, client, view='sendtextapi', kws=kws)
    check_pass(text)

    # post json
    value = "tg post json"
    data = dict(chat_id=chat_id, b=2, arg=value, Chinese=u'中文')
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='tg'),
                 data=json.dumps(data), content_type='application/json')
    check_pass()
    assert json.loads(js['result']['result']['text']) == data

    app.config['TELEGRAM_CHAT_ID'] = chat_id

    # post form
    value = "tg post form"
    data = dict(a=1, arg=value, Chinese=u'中文')
    __, js = req(app, client, view='sendtextapi', kws=dict(opt='tg'), data=data)
    check_pass()
    data['a'] = str(data['a'])
    assert json.loads(js['result']['result']['text']) == data


# On win7, set ENABLE_TELEGRAM_ALERT=True to test Telegram seperately
def test_telegram_fail(app, client):
    kws = dict(opt='telegram')

    def check_fail(status_code=None, result=None, token=app.config['TELEGRAM_TOKEN']):
        assert js['status'] == 'error'
        if status_code is not None:
            assert js['status_code'] == status_code
            assert js['url'] == 'https://api.telegram.org/bot%s/sendMessage' % token
        if result is not None:
            assert js['result'] == result
        assert js['when']

    # TELEGRAM_TOKEN unset
    token = app.config['TELEGRAM_TOKEN']
    app.config['TELEGRAM_TOKEN'] = ''
    req(app, client, view='sendtextapi', kws=kws,
        jskws=dict(status=cst.ERROR, result="The TELEGRAM_TOKEN option is unset"))

    if not (token and app.config['ENABLE_TELEGRAM_ALERT']):
        return
    else:
        app.config['TELEGRAM_TOKEN'] = token

    # TELEGRAM_TOKEN invalid
    fake_token = 'fake_token'
    app.config['TELEGRAM_TOKEN'] = fake_token
    __, js = req(app, client, view='sendtextapi', kws=kws)
    result = dict(description="Not Found", error_code=404, ok=False)
    check_fail(status_code=404, result=result, token=fake_token)
    assert js['debug'] == dict(token=fake_token, chat_id=app.config['TELEGRAM_CHAT_ID'], text='test')

    fake_token_ = token + '_'
    app.config['TELEGRAM_TOKEN'] = fake_token_
    __, js = req(app, client, view='sendtextapi', kws=kws)
    result = dict(description="Unauthorized", error_code=401, ok=False)
    check_fail(status_code=401, result=result, token=fake_token_)
    assert js['debug'] == dict(token=fake_token_, chat_id=app.config['TELEGRAM_CHAT_ID'], text='test')

    app.config['TELEGRAM_TOKEN'] = token

    # TELEGRAM_CHAT_ID invalid
    chat_id = app.config['TELEGRAM_CHAT_ID']
    fake_chat_id = 0
    app.config['TELEGRAM_CHAT_ID'] = fake_chat_id
    __, js = req(app, client, view='sendtextapi', kws=kws)
    check_fail(status_code=400, result=dict(description="Bad Request: chat not found", error_code=400, ok=False))
    assert js['debug'] == dict(token=token, chat_id=fake_chat_id, text='test')

    fake_chat_id_ = chat_id - 1
    app.config['TELEGRAM_CHAT_ID'] = fake_chat_id_
    __, js = req(app, client, view='sendtextapi', kws=kws)
    check_fail(status_code=400, result=dict(description="Bad Request: chat not found", error_code=400, ok=False))
    assert js['debug'] == dict(token=token, chat_id=fake_chat_id_, text='test')
