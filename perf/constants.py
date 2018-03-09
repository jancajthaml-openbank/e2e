#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
  limit = int(os.getenv('MAX_PARALLELISM', '100'))
except ValueError:
  limit = 200

try:
  nodes = int(os.getenv('NODES', 1))
except ValueError:
  nodes = 1

tty = os.getenv('TTY', 'yes') == 'yes'
tenant = os.getenv('TENANT', 'test')

hostname = os.getenv('HTTP_ENTRYPOINT', '127.0.0.1:8080')
site = 'http://' + hostname

def debug(msg):
  sys.stdout.write('\033[97m  debug | \033[0m{0}\n'.format(msg))
  if tty:
    sys.stdout.flush()

def info(msg):
  sys.stdout.write('\033[95m   info | \033[0m{0}\n'.format(msg))
  if tty:
    sys.stdout.flush()

def progress(msg):
  if tty:
    sys.stdout.write('\033[95m   info | \033[0m{0}\r'.format(msg))
    sys.stdout.flush()

def error(msg):
  sys.stdout.write('\033[91m! error | {0}\033[0m\n'.format(msg))
  if tty:
    sys.stdout.flush()

def success(msg):
  sys.stdout.write('\033[92m   pass | {0}\033[0m\n'.format(msg))
  if tty:
    sys.stdout.flush()

def warn(msg):
  sys.stdout.write('\033[93m   warn | {0}\033[0m\n'.format(msg))
  if tty:
    sys.stdout.flush()

def took(msg, elapsed, units, cb = info):
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

  if tty:
    sys.stdout.flush()

