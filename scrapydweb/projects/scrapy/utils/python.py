# coding: utf8
import errno

def retry_on_eintr(function, *args, **kw):
    """Run a function and retry it while getting EINTR errors"""
    while True:
        try:
            return function(*args, **kw)
        except IOError as e:
            if e.errno != errno.EINTR:
                raise
