#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from queue import Queue
from threading import Thread, Event
from time import sleep

_NPROCESSORS_ONLN = int(subprocess.check_output(["getconf", "_NPROCESSORS_ONLN"]).strip()) * 6

class Worker(Thread):

  def __init__(self, name, queue, abort, idle):
    super(Worker, self).__init__()
    self.name = name
    self.queue = queue
    self.abort = abort
    self.idle = idle
    self.daemon = True
    self.start()

  def run(self) -> None:
    while not self.abort.is_set():
      try:
        func, args, kwargs = self.queue.get(False)
        self.idle.clear()
      except Exception:
        self.idle.set()
        continue
      try:
        func(*args, **kwargs)
      except KeyboardInterrupt as ex:
        self.abort.set()
      except Exception:
        pass
      finally:
        self.queue.task_done()

class Pool(object):

  def __init__(self):
    self.queue = Queue(0)
    self.thread_count = _NPROCESSORS_ONLN
    self.aborts = []
    self.idles = []
    self.threads = []

  def __del__(self) -> None:
    self.abort()

  def run(self) -> bool:
    while self.alive():
      sleep(0.1)

    self.aborts = []
    self.idles = []
    self.threads = []
    for n in range(self.thread_count):
      abort = Event()
      idle = Event()
      self.aborts.append(abort)
      self.idles.append(idle)
      self.threads.append(Worker('thread-%d' % n, self.queue, abort, idle))
    return True

  def enqueue(self, func, *args, **kargs) -> None:
    self.queue.put((func, args, kargs))

  def join(self) -> None:
    self.queue.join()

  def abort(self) -> None:
    for a in self.aborts:
      a.set()
    while self.alive():
      sleep(0.1)

  def alive(self) -> bool:
    for t in self.threads:
      if t.is_alive():
        return True
    return False

  def idle(self) -> bool:
    for i in self.idles:
      if not i.is_set():
        return False
    return True

  def done(self):
    return self.queue.empty()
