#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import threading
import sys
import os
import stat
import shutil
import fcntl
import termios
import struct
import copy
import signal
import time
import fcntl
from functools import partial


this = sys.modules[__name__]

fd = sys.stdin.fileno()
old = termios.tcgetattr(fd)
new = copy.deepcopy(old)
new[3] &= ~termios.ICANON & ~termios.ECHO

this.__progress_running = False

termios.tcsetattr(fd, termios.TCSANOW, new)

__TTY = sys.stdout.isatty() and (int(os.environ.get('CI', 0)) == 0)

_, term_w, _, _ = struct.unpack('HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))
buster = (' '*term_w)


def interrupt_stdout() -> None:
  termios.tcsetattr(fd, termios.TCSAFLUSH, old)
  if this.__progress_running and __TTY:
    sys.stdout.write('\n')
    sys.stdout.flush()
  this.__progress_running = False

def debug(msg) -> None:
  this.__progress_running = False
  if isinstance(msg, str):
    sys.stdout.write('\033[97m  debug | \033[0m{0}\033[K\n'.format(msg))
    sys.stdout.flush()
  elif isinstance(msg, collections.Iterable) and len(msg):
    sys.stdout.write('\033[97m  debug | \033[0m{0}\033[K\n'.format(msg[0]))
    for chunk in msg[1:]:
      sys.stdout.write('\033[97m        | \033[0m{0}\033[K\n'.format(chunk))
    sys.stdout.flush()

def info(msg) -> None:
  this.__progress_running = False
  sys.stdout.write('\033[95m   info | \033[0m{0}\033[K\n'.format(msg))
  sys.stdout.flush()

def progress(msg) -> None:
  if not __TTY:
    return
  this.__progress_running = True
  sys.stdout.write('\033[94m        | {0}\033[K\r'.format( msg.rstrip()))
  sys.stdout.flush()

def error(msg) -> None:
  this.__progress_running = False
  sys.stdout.write('\033[91m! error | {0}\033[0m[K\n'.format(msg))
  sys.stdout.flush()

def success(msg) -> None:
  this.__progress_running = False
  sys.stdout.write('\033[92m   pass | {0}\033[0m\033[K\n'.format(msg))
  sys.stdout.flush()

def warn(msg) -> None:
  this.__progress_running = False
  sys.stdout.write('\033[93m   warn | {0}\033[0m\033[K\n'.format(msg))
  sys.stdout.flush()


class timeit():

  def __init__(self, label):
    self.__label = label

  def __call__(self, f, *args, **kwargs):
    self.__enter__()
    result = f(*args, **kwargs)
    self.__exit__()
    return result

  def __enter__(self):
    self.ts = time.time()
    sys.stdout.write('\033[95m   info | \033[0mstarting {0}\033[K\n'.format(self.__label))
    sys.stdout.flush()

  def __exit__(self, exception_type, exception_value, traceback):
    if exception_type == KeyboardInterrupt:
      sys.stdout.write('\033[0m')
      sys.stdout.flush()
      return

    te = time.time()
    sys.stdout.write('\033[90m          {0} took {1}\033[0m\n'.format(self.__label, human_readable_duration((te - self.ts)*1e3)))
    sys.stdout.flush()

def human_readable_duration(ms):
  if ms < 1:
    return "0 ms"

  s, ms = divmod(ms, 1e3)
  m, s = divmod(s, 60)
  h, m = divmod(m, 60)

  h = int(h)
  m = int(m)
  s = int(s)
  ms = int(ms)

  return ' '.join(u'{h}{m}{s}{ms}'.format(
    h=str(h) + " h " if h > 0 else '',
    m=str(m) + " m " if m > 0 else '',
    s=str(s) + " s " if s > 0 else '',
    ms=str(ms) + " ms " if ms > 0 else ''
  ).strip().split(" ")[:4])

class with_deadline():

  def __init__(self, timeout=None):
    if not isinstance(timeout, int):
      raise ValueError("invalid timeout")
    self.__timeout = timeout
    self.__ready = False
    self.__fn = lambda *args: None

  def __get__(self, instance, *args):
    return partial(self.__call__, instance)

  def __call__(self, *args, **kwargs):
    if not self.__ready:
      self.__fn = args[0]
      self.__ready = True
      return self

    with self:
      return self.__fn(*args, **kwargs)

  def __enter__(self):
    def handler(signum, frame):
      raise TimeoutError()

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(self.__timeout)

  def __exit__(self, *args):
    signal.alarm(0)

# fixme move under os_utils module
def clear_dir(path_) -> None:
  if not os.path.exists(path_):
    os.makedirs(path_)
    return

  def __remove_readonly(fn, p, excinfo):
    if fn is os.rmdir:
      os.chmod(p, stat.S_IWRITE)
      os.rmdir(p)
    elif fn is os.remove:
      os.lchmod(p, stat.S_IWRITE)
      os.remove(p)

  def __is_regular(p):
    try:
      mode = os.lstat(p).st_mode
    except os.error:
      mode = 0
    return stat.S_ISDIR(mode)

  if __is_regular(path_):
    for name in os.listdir(path_):
      fullpath = os.path.join(path_, name)
      if __is_regular(fullpath):
        shutil.rmtree(fullpath, onerror=__remove_readonly)
      else:
        try:
          os.remove(fullpath)
        except OSError:
          os.lchmod(fullpath, stat.S_IWRITE)
          os.remove(fullpath)
  else:
    raise OSError("Cannot call clear via symbolic link to a directory")


class ProgressCounter():

  def __init__(self) -> None:
    self._success = 0
    self._failure = 0
    self._progress = 0
    self._lock = threading.Lock()

  def ok(self) -> int:
    with self._lock:
      self._success += 1
      self._progress += 1
      return self._success

  def fail(self) -> int:
    with self._lock:
      self._failure += 1
      self._progress += 1
      return self._progress

  @property
  def success(self) -> int:
    return self._success

  @property
  def failure(self) -> int:
    return self._failure

  @property
  def progress(self) -> int:
    return self._progress


class Counter():

  def __init__(self, value=0) -> None:
    self._value = value
    self._lock = threading.Lock()

  def reset(self) -> int:
    with self._lock:
      self._value = 0
      return self._value

  def inc(self) -> int:
    with self._lock:
      self._value += 1
      return self._value

  def dec(self) -> int:
    with self._lock:
      self._value -= 1
      return self._value

  @property
  def value(self) -> int:
    return self._value

  @value.setter
  def value(self, v) -> int:
    with self._lock:
      self._value = v
      return self._value

