#!/usr/bin/env python

import json
import time
import os

from threading import Thread, Event

class MetricsAggregator(Thread):

  def __init__(self, path):
    super(MetricsAggregator, self).__init__()
    self._stop_event = Event()
    self.__store = {}
    self.__path = path

  def stop(self) -> None:
    self._stop_event.set()

  def __process_change(self) -> None:
    if not os.path.isfile(self.__path):
      return
    try:
      with open(self.__path, mode='r', encoding="ascii") as f:
        self.__store[str(int(time.time()*1000))] = json.load(f)
    except:
      pass

  def get_metrics(self) -> dict:
    store = {}
    store[self.__path] = self.__store.copy()
    return store

  def run(self) -> None:
    while not self._stop_event.is_set():
      time.sleep(0.5)
      self.__process_change()
    self.__process_change()
