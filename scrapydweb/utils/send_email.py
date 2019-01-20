# coding: utf8
from email.mime.text import MIMEText
import json
import smtplib
import sys
import time


def printf(value, warn=False):
    prefix = "!!!" if warn else ">>>"
    print("%s %s" % (prefix, value))


# https://stackoverflow.com/a/27515833/10517783 How to send an email with Gmail as provider using Python?
# https://stackoverflow.com/a/26053352/10517783 Python smtplib proxy support
def send_email(**kwargs):
    to_retry = kwargs.get('to_retry', False)
    need_debug = kwargs.get('need_debug', False)

    smtp_server = kwargs['smtp_server']
    smtp_port = kwargs['smtp_port']
    smtp_over_ssl = kwargs['smtp_over_ssl']
    smtp_connection_timeout = kwargs['smtp_connection_timeout']
    from_addr = kwargs['from_addr']
    email_password = kwargs['email_password']
    to_addrs = kwargs['to_addrs']
    subject = kwargs['subject']
    content = kwargs['content']

    msg = MIMEText(u'%s\n%s' % (time.ctime(), content), 'plain', 'utf-8')
    msg['From'] = from_addr
    msg['Subject'] = u'{} {}'.format(time.strftime('%H:%M'), subject)

    result = False
    try:
        if smtp_over_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=smtp_connection_timeout)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=smtp_connection_timeout)
            server.ehlo()
            server.starttls()
        if need_debug:
            server.set_debuglevel(1)  # For debug
        server.login(from_addr, email_password)
        server.sendmail(from_addr, to_addrs, msg.as_string())
    except Exception as err:
        printf("FAIL to send email: %s" % subject)
        try:
            printf("FAIL reason: %s" % err.args[-1].decode('utf8'))
        except:
            try:
                printf("FAIL reason: %s" % err.args[-1].decode('gbk'))
            except:
                printf("FAIL reason: %s" % err)
        if to_retry:
            kwargs.update({'to_retry': False, 'need_debug': True})
            printf("Retrying...")
            send_email(**kwargs)
    else:
        result = True
        printf("Email sent: %s" % subject)
    finally:
        try:
            server.quit()
        except:
            pass

    return result


if __name__ == '__main__':
    send_email(**json.loads(sys.argv[1]))
