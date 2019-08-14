# coding: utf-8
import atexit
from ctypes import cdll
import logging
import os
import platform
import signal
from subprocess import Popen
import sys

from ..common import json_dumps


logger = logging.getLogger(__name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


# https://stackoverflow.com/a/13256908/10517783
# https://stackoverflow.com/a/23587108/10517783
# http://evans.io/legacy/posts/killing-child-processes-on-parent-exit-prctl/
class PrCtlError(Exception):
    pass


def on_parent_exit(signame):
    """
    Return a function to be run in a child process which will trigger
    SIGNAME to be sent when the parent process dies
    """
    # On Windows, signal() can only be called with SIGABRT, SIGFPE, SIGILL, SIGINT, SIGSEGV, or SIGTERM.
    signum = getattr(signal, signame)  # SIGTERM 15  SIGKILL 9

    def set_parent_exit_signal():
        # Constant taken from http://linux.die.net/include/linux/prctl.h
        PR_SET_PDEATHSIG = 1
        # http://linux.die.net/man/2/prctl
        result = cdll['libc.so.6'].prctl(PR_SET_PDEATHSIG, signum)
        if result != 0:
            raise PrCtlError('prctl failed with error code %s' % result)

    return set_parent_exit_signal


# https://stackoverflow.com/a/19448255/10517783
def kill_child(proc, title=''):
    proc.kill()
    # A None value indicates that the process has not terminated yet.
    # A negative value -N indicates that the child was terminated by signal N (Unix only).
    logger.warning('%s subprocess (pid: %s) killed with returncode: %s', title, proc.pid, proc.wait())


def init_logparser(config):
    logparser_subprocess = start_logparser(config)
    logparser_pid = logparser_subprocess.pid
    logger.info("Running LogParser in the background with pid: %s", logparser_pid)
    atexit.register(kill_child, logparser_subprocess, 'LogParser')
    return logparser_pid


def start_logparser(config):
    args = [
        sys.executable,
        '-m',
        'logparser.run',
        '-dir',
        config['LOCAL_SCRAPYD_LOGS_DIR'],
        '--main_pid',
        str(config['MAIN_PID']),
    ]

    if platform.system() == 'Linux':
        kwargs = dict(preexec_fn=on_parent_exit('SIGKILL'))  # 'SIGTERM' 'SIGKILL'
        try:
            logparser_subprocess = Popen(args, **kwargs)
        except Exception as err:
            logger.error(err)
            logparser_subprocess = Popen(args)
    else:
        logparser_subprocess = Popen(args)

    return logparser_subprocess


def init_poll(config):
    poll_subprocess = start_poll(config)
    poll_pid = poll_subprocess.pid
    logger.info("Start polling job stats for monitor & alert in the background with pid: %s", poll_pid)
    atexit.register(kill_child, poll_subprocess, 'Poll')
    return poll_pid


def start_poll(config):
    args = [
        sys.executable,
        os.path.join(CURRENT_DIR, 'poll.py'),

        config['URL_SCRAPYDWEB'],
        config.get('USERNAME', '') if config.get('ENABLE_AUTH', False) else '',
        config.get('PASSWORD', '') if config.get('ENABLE_AUTH', False) else '',
        json_dumps(config.get('SCRAPYD_SERVERS', ['127.0.0.1'])),
        json_dumps(config.get('SCRAPYD_SERVERS_AUTHS', [None])),
        str(config.get('POLL_ROUND_INTERVAL', 300)),
        str(config.get('POLL_REQUEST_INTERVAL', 10)),
        str(config['MAIN_PID']),
        str(config.get('VERBOSE', False))
    ]

    # 'Windows':
    # AttributeError: module 'signal' has no attribute 'SIGKILL'
    # ValueError: preexec_fn is not supported on Windows platforms
    # macOS('Darwin'):
    # subprocess.SubprocessError: Exception occurred in preexec_fn.
    # OSError: dlopen(libc.so.6, 6): image not found
    if platform.system() == 'Linux':
        kwargs = dict(preexec_fn=on_parent_exit('SIGKILL'))  # 'SIGTERM' 'SIGKILL'
        try:
            poll_subprocess = Popen(args, **kwargs)
        except Exception as err:
            logger.error(err)
            poll_subprocess = Popen(args)
    else:
        poll_subprocess = Popen(args)

    return poll_subprocess
