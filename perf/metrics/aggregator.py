#!/usr/bin/env python

import json
import time
import os
from inotify_simple import INotify, flags

from threading import Lock, Thread, Event

class MetricsAggregator(Thread):

  def __init__(self, path):
    super(MetricsAggregator, self).__init__()
    self._stop_event = Event()
    self.__store = {}
    self.__path = path
    self.__watcher = INotify()

  def stop(self) -> None:
    self._stop_event.set()

  def __process_change(self, path) -> None:
    with open(path, mode='r', encoding="ascii") as f:
      self.__store[str(int(time.time()*1000))] = json.load(f)

  def get_metrics(self) -> dict:
    store = {}
    store[self.__path] = self.__store
    return store

  def run(self) -> None:
    dirname = os.path.dirname(self.__path)
    self.__watcher.add_watch(dirname, flags.CREATE | flags.MODIFY | flags.MOVED_TO)
    while not self._stop_event.is_set():
      for event in self.__watcher.read(timeout=600):
        if dirname + '/' + event.name == self.__path:
          self.__process_change(self.__path)

