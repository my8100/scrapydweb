# coding: utf-8
import re

from flask import render_template, request, url_for

from ...utils.send_email import send_email
from ..baseview import BaseView


class SendTextView(BaseView):

    def __init__(self):
        super(SendTextView, self).__init__()

        self.template = 'scrapydweb/send_text.html'

    def dispatch_request(self, **kwargs):
        kwargs = dict(
            node=self.node,
            url_slack=url_for('sendtextapi', opt='slack', channel_chatid_subject=None, text='some-text'),
            url_telegram=url_for('sendtextapi', opt='telegram', channel_chatid_subject=None, text='some-text'),
            url_email=url_for('sendtextapi', opt='email', channel_chatid_subject=None, text='some-text'),
        )
        return render_template(self.template, **kwargs)


class SendTextApiView(BaseView):
    # https://api.slack.com/methods/chat.postMessage
    # https://www.codementor.io/garethdwyer/building-a-telegram-bot-using-python-part-1-goi5fncay
    # slack_help = 'https://api.slack.com/apps'
    # telegram_help = 'https://core.telegram.org/bots#6-botfather'

    def __init__(self):
        super(SendTextApiView, self).__init__()

        self.opt = self.view_args['opt']
        self.opt = 'telegram' if self.opt == 'tg' else self.opt
        # https://stackoverflow.com/questions/10434599/get-the-data-received-in-a-flask-request
        # request.values: combined args and form, preferring args if keys overlap
        self.form = request.json or request.form

        if self.opt == 'email':
            self.channel_chatid_subject = (self.view_args['channel_chatid_subject']
                                           or request.args.get('subject', None)
                                           or self.form.get('subject', self.EMAIL_SUBJECT))
            # request.json['recipients'] could be a list type instead of a string type
            recipients = re.findall(r'[^\s"\',;\[\]]+@[^\s"\',;\[\]]+',
                                    request.args.get('recipients', '') or str(self.form.get('recipients', '')))
            self.EMAIL_KWARGS['email_recipients'] = recipients or self.EMAIL_RECIPIENTS
        elif self.opt == 'slack':
            self.channel_chatid_subject = (self.view_args['channel_chatid_subject']
                                           or request.args.get('channel', None)
                                           or self.form.get('channel', self.SLACK_CHANNEL))  # 'general'
        else:
            self.channel_chatid_subject = (self.view_args['channel_chatid_subject']
                                           or request.args.get('chat_id', None)
                                           or self.form.get('chat_id', self.TELEGRAM_CHAT_ID))
        self.logger.debug('channel_chatid_subject: %s', self.channel_chatid_subject)

        self.text = self.view_args['text'] or request.args.get('text', None)
        if not self.text:
            self.text = self.json_dumps(self.form) if self.form else 'test'
        self.logger.debug('text: %s', self.text)

        self.js = {}
        self.tested = False  # For test only

    def dispatch_request(self, **kwargs):
        if self.opt == 'email':
            self.send_email()
        elif self.opt == 'slack':
            self.send_slack()
        elif self.opt == 'telegram':
            self.send_telegram()
        self.js['when'] = self.get_now_string(True)
        return self.json_dumps(self.js, as_response=True)

    def send_email(self):
        if not self.EMAIL_PASSWORD:
            self.js = dict(status=self.ERROR, result="The EMAIL_PASSWORD option is unset")
            return
        self.EMAIL_KWARGS['subject'] = self.channel_chatid_subject
        self.EMAIL_KWARGS['content'] = self.text
        result, reason = send_email(to_retry=True, **self.EMAIL_KWARGS)
        if result is True:
            self.logger.debug("Sent to %s via Email", self.EMAIL_KWARGS['email_recipients'])
            self.js = dict(status=self.OK,
                           result=dict(reason=reason, sender=self.EMAIL_KWARGS['email_sender'],
                                       recipients=self.EMAIL_KWARGS['email_recipients'],
                                       subject=self.channel_chatid_subject, text=self.text))
        else:
            self.js = dict(status=self.ERROR, result=dict(reason=reason), debug=self.EMAIL_KWARGS)
            self.logger.error("Fail to send text via Email:\n%s", self.json_dumps(self.js))

    def send_slack(self):
        if not self.SLACK_TOKEN:
            self.js = dict(status=self.ERROR, result="The SLACK_TOKEN option is unset")
            return
        url = 'https://slack.com/api/chat.postMessage'
        data = dict(token=self.SLACK_TOKEN, channel=self.channel_chatid_subject, text=self.text)
        status_code, js = self.make_request(url, data=data, check_status=False)
        for key in ['auth', 'status', 'status_code', 'url', 'when']:
            js.pop(key, None)
        self.js = dict(url=url, status_code=status_code, result=js)
        # {"ok":false,"error":"invalid_auth"}
        # {"ok":false,"error":"channel_not_found"}
        # {"ok":false,"error":"no_text"}
        if js.get('ok', False):
            self.logger.debug("Sent to bot %s via Slack", js.get('message', {}).get('username', ''))
            self.js['status'] = self.OK
        else:
            self.js['status'] = self.ERROR
            if self.SLACK_TOKEN:
                self.js['debug'] = dict(token=self.SLACK_TOKEN, channel=self.channel_chatid_subject,
                                        text=self.text)
            self.logger.error("Fail to send text via Slack:\n%s", self.json_dumps(self.js))

    def send_telegram(self):
        if not self.TELEGRAM_TOKEN:
            self.js = dict(status=self.ERROR, result="The TELEGRAM_TOKEN option is unset")
            return
        url = 'https://api.telegram.org/bot%s/sendMessage' % self.TELEGRAM_TOKEN
        data = dict(text=self.text, chat_id=self.channel_chatid_subject)
        status_code, js = self.make_request(url, data=data, check_status=False)

        for key in ['auth', 'status', 'status_code', 'url', 'when']:
            js.pop(key, None)
        self.js = dict(url=url, status_code=status_code, result=js)
        if js.get('ok', False):
            self.logger.debug("Sent to %s via Telegram", js.get('result', {}).get('chat', {}).get('first_name', ''))
            self.js['status'] = self.OK
        # {"ok":false,"error_code":400,"description":"Bad Request: chat not found"}
        else:
            self.js['status'] = self.ERROR
            if self.TELEGRAM_TOKEN:
                self.js['debug'] = dict(token=self.TELEGRAM_TOKEN, chat_id=self.channel_chatid_subject,
                                        text=self.text)
            self.logger.error("Fail to send text via Telegram:\n%s", self.json_dumps(self.js))
