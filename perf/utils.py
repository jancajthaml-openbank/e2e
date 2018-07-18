#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import threading
import sys
import subprocess
import time
import os
import stat
import shutil
import termios
import copy
import signal
from functools import partial

this = sys.modules[__name__]

fd = sys.stdin.fileno()
old = termios.tcgetattr(fd)
new = copy.deepcopy(old)
new[3] = new[3] & ~termios.ECHO

this.__progress_running = False

termios.tcsetattr(fd, termios.TCSADRAIN, new)

def interrupt_stdout() -> None:
  termios.tcsetattr(fd, termios.TCSADRAIN, old)
  if this.__progress_running and sys.stdout.isatty():
    sys.stdout.write('\n')
    sys.stdout.flush()
  this.__progress_running = False

def debug(msg) -> None:
  this.__progress_running = False
  if isinstance(msg, str):
    sys.stdout.write('\033[97m  debug | \033[0m{0}\n'.format(msg))
    sys.stdout.flush()
  elif isinstance(msg, collections.Iterable) and len(msg):
    sys.stdout.write('\033[97m  debug | \033[0m{0}\n'.format(msg[0]))
    for chunk in msg[1:]:
      sys.stdout.write('\033[97m        | \033[0m{0}\n'.format(chunk))
    sys.stdout.flush()

def info(msg) -> None:
  this.__progress_running = False
  sys.stdout.write('\033[95m   info | \033[0m{0}\n'.format(msg))
  sys.stdout.flush()

def progress(msg) -> None:
  if not sys.stdout.isatty():
    return
  this.__progress_running = True
  sys.stdout.write('\033[94m        | {0}\r'.format(msg))
  sys.stdout.flush()

def error(msg) -> None:
  this.__progress_running = False
  sys.stdout.write('\033[91m! error | {0}\033[0m\n'.format(msg))
  sys.stdout.flush()

def success(msg) -> None:
  this.__progress_running = False
  sys.stdout.write('\033[92m   pass | {0}\033[0m\n'.format(msg))
  sys.stdout.flush()

def warn(msg) -> None:
  this.__progress_running = False
  sys.stdout.write('\033[93m   warn | {0}\033[0m\n'.format(msg))
  sys.stdout.flush()

def took(msg, elapsed, units, cb = info) -> None:
  this.__progress_running = False
  if not units:
    units = 1

  # fixme measure average per unit

  def time_to_s(e):
    h = e // 3600 % 24
    m = e // 60 % 60
    s = int(e % 60)
    ms = int((e % 60) * 1000) - (s * 1000)
    ys = int((e % 60) * 1000000) - (ms * 1000)

    if h:
      c = '%01d hour %01d min %01d sec %01d ms ' % (h, m, s, ms)
    elif m:
      c = '%01d min %01d sec %01d ms ' % (m, s, ms)
    elif s:
      c = '%01d sec %01d ms ' % (s, ms)
    elif ms:
      c = '%01d ms' % ms
    else:
      c = '%3.4f ys' % ys

    return c

  if msg == '':
    if units == 1:
      sys.stdout.write('\033[90m          {0}\033[0m\n'.format(time_to_s(elapsed)))
    else:
      sys.stdout.write('\033[90m          {0} ... {1} per unit\033[0m\n'.format(time_to_s(elapsed), time_to_s(elapsed / units)))
  else:
    cb(msg)
    if units == 1:
      sys.stdout.write('\033[90m          {0}\033[0m\n'.format(time_to_s(elapsed)))
    else:
      sys.stdout.write('\033[90m          {0} ... {1} per unit\033[0m\n'.format(time_to_s(elapsed), time_to_s(elapsed / units)))

  sys.stdout.flush()

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

# fixme optimise this to count (passed/failed) + progress with one increment (lock) instead of two
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
    with self._lock:
      return self._value

  @value.setter
  def value(self, v) -> int:
    with self._lock:
      self._value = v
      return self._value

