#!/usr/bin/env python
# -*- coding: utf-8 -*-

def parametrized(dec):
    def layer(*args, **kwargs):
        def repl(f):
            return dec(f, *args, **kwargs)
        return repl
    return layer

@parametrized
def with_deadline(f=None, timeout=None):
    if f is None:
        return
    if timeout is None:
        raise ValueError("you must define deadline in seconds")

    import signal

    def handler(signum, frame):
        raise TimeoutError()

    def aux(*xs, **kws):
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout)
        failed = False
        try:
            result = f(*xs, **kws)
        except TimeoutError:
            result = None
            failed = True
        finally:
            signal.alarm(0)

        if failed:
          raise RuntimeError("function timed out after {0} seconds".format(timeout))

        return result
    return aux
