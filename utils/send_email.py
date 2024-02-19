# coding: utf-8
from collections import OrderedDict
from email.mime.text import MIMEText
import json
import logging
import smtplib
import sys
import time


logger = logging.getLogger('scrapydweb.utils.send_email')  # __name__
logger.setLevel(logging.DEBUG)


# https://stackoverflow.com/a/27515833/10517783 How to send an email with Gmail as provider using Python?
# https://stackoverflow.com/a/26053352/10517783 Python smtplib proxy support
def send_email(**kwargs):
    to_retry = kwargs.get('to_retry', False)
    need_debug = kwargs.get('need_debug', False)

    email_username = kwargs['email_username']
    email_password = kwargs['email_password']
    email_sender = kwargs['email_sender']
    email_recipients = kwargs['email_recipients']
    smtp_server = kwargs['smtp_server']
    smtp_port = kwargs['smtp_port']
    smtp_over_ssl = kwargs['smtp_over_ssl']
    smtp_connection_timeout = kwargs['smtp_connection_timeout']
    subject = kwargs['subject']
    content = kwargs['content']
    # https://stackoverflow.com/questions/6921699/can-i-get-json-to-load-into-an-ordereddict/6921760#6921760
    # data = json.loads('{"foo":1, "bar": 2}', object_pairs_hook=OrderedDict)
    # In log.py : ensure_ascii=True
    # json.loads('abc') -> JSONDecodeError
    try:
        content = json.dumps(json.loads(content, object_pairs_hook=OrderedDict),
                             sort_keys=False, indent=4, ensure_ascii=False)
    except ValueError:
        pass

    msg = MIMEText(u'%s\n%s' % (time.ctime(), content), 'plain', 'utf-8')
    msg['From'] = email_sender
    msg['Subject'] = u'{} {}'.format(time.strftime('%H:%M'), subject)

    server = None
    result = False
    reason = ''
    try:
        if smtp_over_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=smtp_connection_timeout)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=smtp_connection_timeout)
            server.ehlo()
            server.starttls()
        if need_debug:
            server.set_debuglevel(1)  # For debug
        server.login(email_username, email_password)
        server.sendmail(email_sender, email_recipients, msg.as_string())
    except Exception as err:
        logger.error("Fail to send email: %s", subject)
        try:
            reason = err.args[-1].decode('utf8')
        except:
            try:
                reason = err.args[-1].decode('gbk')
            except:
                reason = str(err)
        logger.info("Fail reason: %s", reason)
        if to_retry:
            kwargs.update(to_retry=False, need_debug=True)
            logger.debug("Retrying...")
            time.sleep(3)
            return send_email(**kwargs)
    else:
        result = True
        reason = "Sent"
        logger.info("Email sent: %s", subject)
    finally:
        if server is not None:
            try:
                server.quit()
            except:
                pass

    return result, reason


if __name__ == '__main__':
    # To avoid logging twice when importing the send_email function to send email.
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(fmt="[%(asctime)s] %(levelname)-8s in %(name)s: %(message)s")
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)

    send_email(**json.loads(sys.argv[1]))
