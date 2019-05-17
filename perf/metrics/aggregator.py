#!/usr/bin/env python

import json
import time
import os
from inotify_simple import INotify, flags

from threading import Lock, Thread, Event

class MetricsAggregator(Thread):

  def __init__(self, path, manager):
    super(MetricsAggregator, self).__init__()
    self._stop_event = Event()
    self.__manager = manager
    self.__store = {}
    self.__path = path
    self.__watcher = INotify()
    self.__lock = Lock()
    self.__store = {}

  def stop(self) -> None:
    self._stop_event.set()

  def stopped(self) -> bool:
    return self._stop_event.is_set()

  def __process_change(self, path) -> None:
    with self.__lock:
      if not (path in self.__store):
        self.__store[path] = {}
      try:
        with open(path, mode='r', encoding="ascii") as f:
          self.__store[path][str(int(time.time()*1000))] = json.load(f)
      except IOError:
        pass

  def get_metrics(self):
    return self.__store

  def run(self) -> None:
    self.__watcher.add_watch(self.__path, flags.CREATE | flags.MODIFY | flags.MOVED_TO)

    while not self.stopped():
      for event in self.__watcher.read(timeout=100):
        if not event.name.endswith('temp'):
          self.__process_change(os.path.join(self.__path, event.name))
