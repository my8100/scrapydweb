# coding: utf8
import time
import json
import signal
from ctypes import cdll

import requests
from flask import current_app as app
from flask import Response


session = requests.Session()


def make_request(url, data=None, timeout=60, api=True, log=True, auth=None):
    """
    :param api: return dict if set True, else text
    """
    try:
        if log:
            if 'addversion.json' in url and data:
                app.logger.debug('>>>>> POST %s' % url)
                app.logger.debug(json_dumps(dict(project=data['project'], version=data['version'],
                                                egg="%s bytes binary egg file" % len(data['egg']))))
            else:
                app.logger.debug('>>>>> %s %s' % ('POST' if data else 'GET', url))
                if data:
                    app.logger.debug(json_dumps(data))
        if data:
            r = session.post(url, data=data, timeout=timeout, auth=auth)
        else:
            r = session.get(url, timeout=timeout, auth=auth)
        r.encoding = 'utf8'
    except Exception as err:
        if log:
            app.logger.error('!!!!! %s %s' % (err.__class__.__name__, err))
        if api:
            return -1, {'url': url, 'auth': auth, 'status_code': -1,
                        'status': 'error', 'message': str(err)}
        else:
            return -1, str(err)
    else:
        if api:
            try:
                r_json = r.json()
            except json.JSONDecodeError: # When Scrapyd server reboot, listprojects got 502 html
                r_json = {'status': 'error', 'message': r.text}
            finally:
                r_json.update(dict(url=url, auth=auth, status_code=r.status_code, when=time.ctime()))
                if log:
                    sign = '!!!!! ' if (r.status_code != 200 or r_json.get('status') != 'ok') else '<<<<< '
                    app.logger.debug('%s%s %s' % (sign, r.status_code, url))
                    app.logger.debug(json_dumps(r_json))

                return r.status_code, r_json
        else:
            if r.status_code == 200:
                front = r.text[:min(100, len(r.text))].replace('\n', '')
                back = r.text[-min(100, len(r.text)):].replace('\n', '')
                if log:
                    app.logger.debug('<<<<< %s %s\n...%s' % (r.status_code, front, back))
            else:
                if log:
                    app.logger.debug('!!!!! %s %s' % (r.status_code, r.text))

            return r.status_code, r.text


def json_dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=4, sort_keys=True)


# http://flask.pocoo.org/snippets/category/authentication/
def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response("<script>alert('FAIL to login. Basic auth is enabled since ScrapydWeb is running with argument "
                    '''"--username USERNAME" and "--password PASSWORD"');</script>''',
                    401, {'WWW-Authenticate': 'Basic realm="ScrapydWeb Basic Auth Required"'})


# https://stackoverflow.com/a/19448255/10517783
def kill_child(proc):
    proc.kill()
    # A None value indicates that the process hasn’t terminated yet.
    # A negative value -N indicates that the child was terminated by signal N (Unix only).
    print('Caching subprocess (pid: %s) killed with returncode: %s' % (proc.pid, proc.wait()))


# https://stackoverflow.com/a/13256908/10517783
# https://stackoverflow.com/a/23587108/10517783
# http://evans.io/legacy/posts/killing-child-processes-on-parent-exit-prctl/

# Constant taken from http://linux.die.net/include/linux/prctl.h
PR_SET_PDEATHSIG = 1

class PrCtlError(Exception):
    pass


def on_parent_exit(signame):
    """
    Return a function to be run in a child process which will trigger
    SIGNAME to be sent when the parent process dies
    """
    # On Windows, signal() can only be called with SIGABRT, SIGFPE, SIGILL, SIGINT, SIGSEGV, or SIGTERM.
    signum = getattr(signal, signame) # SIGTERM 15  SIGKILL 9
    def set_parent_exit_signal():
        # http://linux.die.net/man/2/prctl
        result = cdll['libc.so.6'].prctl(PR_SET_PDEATHSIG, signum)
        if result != 0:
            raise PrCtlError('prctl failed with error code %s' % result)
    return set_parent_exit_signal
