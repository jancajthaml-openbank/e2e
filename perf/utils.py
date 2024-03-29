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
from helpers.logger import logger

this = sys.modules[__name__]

fd = sys.stdin.fileno()
old = termios.tcgetattr(fd)
new = copy.deepcopy(old)
new[3] &= ~termios.ICANON & ~termios.ECHO

this.__progress_running = False
this.__last_progress = ""
this.__logger = logger()

termios.tcsetattr(fd, termios.TCSANOW, new)

TTY = (str(os.environ.get('CI', 'false')) == 'false')

if not TTY:
  print()


def interrupt_stdout() -> None:
  termios.tcsetattr(fd, termios.TCSAFLUSH, old)
  if this.__progress_running and __TTY:
    sys.stdout.write('\n')
    sys.stdout.flush()
  this.__progress_running = False


def debug(msg) -> None:
  this.__logger.debug('(PERF) DEBUG {}'.format(msg))
  this.__progress_running = False
  if isinstance(msg, str):
    sys.stdout.write('\033[97m  debug ║ \033[0m{0}\033[K\n'.format(msg))
    sys.stdout.flush()
  elif isinstance(msg, collections.Iterable) and len(msg):
    sys.stdout.write('\033[97m  debug ║ \033[0m{0}\033[K\n'.format(msg[0]))
    for chunk in msg[1:]:
      sys.stdout.write('\033[97m        │ \033[0m{0}\033[K\n'.format(chunk))
    sys.stdout.flush()


def info(msg) -> None:
  this.__logger.info('(PERF) INFO {}'.format(msg))
  this.__progress_running = False
  sys.stdout.write('\033[95m   info ║ \033[0m{0}\033[K\n'.format(msg))
  sys.stdout.flush()


def progress(msg) -> None:
  if this.__last_progress == msg:
    return
  this.__last_progress = msg
  if TTY:
    this.__progress_running = True
    sys.stdout.write('\033[94m        │ {0}\033[K\r'.format(msg.rstrip()))
    sys.stdout.flush()
  else:
    sys.stdout.write('\033[94m        │ {0}\033[K\n'.format(msg.rstrip()))
    sys.stdout.flush()


def error(msg) -> None:
  this.__logger.error('(PERF) ERROR {}'.format(msg))
  this.__progress_running = False
  sys.stdout.write('\033[91m! error ║ {0}\033[0m[K\n'.format(msg))
  sys.stdout.flush()


def success(msg) -> None:
  this.__logger.info('(PERF) SUCCESS {}'.format(msg))
  this.__progress_running = False
  sys.stdout.write('\033[92m   pass ║ {0}\033[0m\033[K\n'.format(msg))
  sys.stdout.flush()


def warn(msg) -> None:
  this.__logger.warning('(PERF) WARNING {}'.format(msg))
  this.__progress_running = False
  sys.stdout.write('\033[93m   warn ║ {0}\033[0m\033[K\n'.format(msg))
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

  def __exit__(self, exception_type, exception_value, traceback):
    if exception_type == KeyboardInterrupt:
      sys.stdout.write('\033[0m')
      sys.stdout.flush()
      return

    te = time.time()
    sys.stdout.write('\033[0m        │\033[90m {0} took {1}\033[0m\n'.format(self.__label, human_readable_duration((te - self.ts)*1e3)))
    sys.stdout.flush()

def human_readable_count(num):
  result = num
  idx = 0
  units = {
    1: 'k',
    2: 'M',
    3: 'G',
    4: 'T',
    5: 'E',
    6: 'P'
  }
  for x in range(len(units)):
    if result < 1000:
      break
    result /= 1000
    idx += 1

  return '{}{}'.format(int(result), units.get(idx, ''))

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
