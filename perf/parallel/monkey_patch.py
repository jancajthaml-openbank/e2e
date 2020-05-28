#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading


def patch_thread_join():
  threading.currentThread()
  mainThreadId = threading.get_ident()
  join_orig = threading.Thread.join
  def patch(threadObj, timeout=None):
    if timeout is None and threading.get_ident() == mainThreadId:
      while threadObj.isAlive():
        join_orig(threadObj, timeout=None)
    else:
      join_orig(threadObj, timeout=timeout)

  threading.Thread.join = patch
