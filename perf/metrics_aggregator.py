#!/usr/bin/env python

import json
import time
import os
from inotify_simple import INotify, flags

from threading import Lock, Thread, Event

class MetricsAggregator(Thread):

  def __init__(self, manager):
    super(MetricsAggregator, self).__init__()
    self._stop_event = Event()
    self.__manager = manager
    self.__store = {}
    self.__lake_watch = INotify()
    self.__ledger_watch = INotify()
    self.__vault_watch = INotify()
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
      else:
        f.close()

  def persist(self, label) -> None:
    with open('{0}/{1}.json'.format('/reports/perf_metrics', label), mode='w', encoding="ascii") as f:
      json.dump(self.__store, f, indent=4, sort_keys=True)

  def run(self) -> None:
    self.__lake_watch.add_watch('/opt/lake/metrics', flags.MODIFY | flags.MOVED_TO)
    self.__ledger_watch.add_watch('/opt/ledger/metrics', flags.MODIFY | flags.MOVED_TO)
    self.__vault_watch.add_watch('/opt/vault/metrics', flags.MODIFY | flags.MOVED_TO)

    while not self.stopped():
      events = []

      for event in self.__lake_watch.read(timeout=100):
        if not event.name.endswith('temp'):
          path = os.path.join('/opt/lake/metrics', event.name)
          self.__process_change(path)

      for event in self.__ledger_watch.read(timeout=100):
        if not event.name.endswith('temp'):
          path = os.path.join('/opt/ledger/metrics', event.name)
          self.__process_change(path)

      for event in self.__vault_watch.read(timeout=100):
        if not event.name.endswith('temp'):
          path = os.path.join('/opt/vault/metrics', event.name)
          self.__process_change(path)
