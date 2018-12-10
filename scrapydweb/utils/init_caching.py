# coding: utf8
import os
import sys
import platform
from subprocess import Popen
import atexit
import signal
from ctypes import cdll

from .utils import printf, json_dumps


CWD = os.path.dirname(os.path.abspath(__file__))


# https://stackoverflow.com/a/19448255/10517783
def kill_child(proc):
    proc.kill()
    # A None value indicates that the process hasn’t terminated yet.
    # A negative value -N indicates that the child was terminated by signal N (Unix only).
    printf('Caching subprocess (pid: %s) killed with returncode: %s' % (proc.pid, proc.wait()), warn=True)


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


def init_caching(config, main_pid):
    if config.get('ENABLE_CACHE', True):
        caching_subprocess = start_caching(config, main_pid)
        caching_pid = caching_subprocess.pid
        printf("Caching HTML for Log and Stats page in the background with pid: %s" % caching_pid)
        atexit.register(kill_child, caching_subprocess)
    else:
        caching_pid = None

    return caching_pid


def start_caching(config, main_pid):
    _bind = config.get('SCRAPYDWEB_BIND', '0.0.0.0')
    _bind = '127.0.0.1' if _bind == '0.0.0.0' else _bind
    args = [
        sys.executable,
        os.path.join(CWD, 'cache.py'),

        str(main_pid),
        _bind,
        str(config.get('SCRAPYDWEB_PORT', 5000)),
        config.get('USERNAME', '') if config.get('ENABLE_AUTH', False) else '',
        config.get('PASSWORD', '') if config.get('ENABLE_AUTH', False) else '',
        json_dumps(config.get('SCRAPYD_SERVERS', ['127.0.0.1'])),
        json_dumps(config.get('SCRAPYD_SERVERS_AUTHS', [None])),
        str(config.get('CACHE_ROUND_INTERVAL', 300)),
        str(config.get('CACHE_REQUEST_INTERVAL', 10)),
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
            caching_subprocess = Popen(args, **kwargs)
        except Exception as err:
            printf(err, warn=True)
            caching_subprocess = Popen(args)
    else:
        caching_subprocess = Popen(args)

    return caching_subprocess
