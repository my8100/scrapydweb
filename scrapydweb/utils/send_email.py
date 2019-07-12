# coding: utf-8
from collections import OrderedDict
from email.mime.text import MIMEText
import json
import logging
import smtplib
import sys
import time


logger = logging.getLogger('scrapydweb.utils.send_email')  # __name__
_handler = logging.StreamHandler()
_formatter = logging.Formatter(fmt="[%(asctime)s] %(levelname)-8s in %(name)s: %(message)s")
_handler.setFormatter(_formatter)
logger.addHandler(_handler)
logger.setLevel(logging.DEBUG)


# https://stackoverflow.com/a/27515833/10517783 How to send an email with Gmail as provider using Python?
# https://stackoverflow.com/a/26053352/10517783 Python smtplib proxy support
def send_email(**kwargs):
    to_retry = kwargs.get('to_retry', False)
    need_debug = kwargs.get('need_debug', False)

    smtp_server = kwargs['smtp_server']
    smtp_port = kwargs['smtp_port']
    smtp_over_ssl = kwargs['smtp_over_ssl']
    smtp_connection_timeout = kwargs['smtp_connection_timeout']
    email_username = kwargs['email_username']
    email_password = kwargs['email_password']
    from_addr = kwargs['from_addr']
    to_addrs = kwargs['to_addrs']
    subject = kwargs['subject']
    content = kwargs['content']
    # https://stackoverflow.com/questions/6921699/can-i-get-json-to-load-into-an-ordereddict/6921760#6921760
    # data = json.loads('{"foo":1, "bar": 2}', object_pairs_hook=OrderedDict)
    # In log.py : ensure_ascii=True
    content = json.dumps(json.loads(content, object_pairs_hook=OrderedDict),
                         sort_keys=False, indent=4, ensure_ascii=False)

    msg = MIMEText(u'%s\n%s' % (time.ctime(), content), 'plain', 'utf-8')
    msg['From'] = from_addr
    msg['Subject'] = u'{} {}'.format(time.strftime('%H:%M'), subject)

    result = False
    server = None
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
        server.sendmail(from_addr, to_addrs, msg.as_string())
    except Exception as err:
        logger.error("Fail to send email: %s", subject)
        try:
            logger.info("Fail reason: %s", err.args[-1].decode('utf8'))
        except:
            try:
                logger.info("Fail reason: %s", err.args[-1].decode('gbk'))
            except:
                logger.info("Fail reason: %s", err)
        if to_retry:
            kwargs.update(to_retry=False, need_debug=True)
            logger.debug("Retrying...")
            send_email(**kwargs)
    else:
        result = True
        logger.info("Email sent: %s", subject)
    finally:
        if server is not None:
            try:
                server.quit()
            except:
                pass

    return result


if __name__ == '__main__':
    send_email(**json.loads(sys.argv[1]))
