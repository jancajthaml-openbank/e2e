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
    self.path = path
    self.__store = {}
    self.__inotify = INotify()
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
          self.__store[path][str(int(time.time()))] = json.load(f)
      except IOError:
        pass
      else:
        f.close()

  def persist(self, label) -> None:
    with open('{0}/all_{1}.json'.format(self.path, label), mode='w', encoding="ascii") as f:
      json.dump(self.__store, f, indent=4, sort_keys=True)

  def run(self) -> None:
    self.__inotify.add_watch(self.path, flags.MODIFY | flags.MOVED_TO)

    while not self.stopped():
      for event in self.__inotify.read(timeout=500):
        if not event.name.endswith("temp") and event.name.startswith("p-"):
          path = event.name and os.path.join(self.path, event.name) or self.path
          self.__process_change(path)
