#!/usr/bin/env python

import json
import time
import os
from metrics.aggregator import MetricsAggregator

class MetricsManager():

  def __init__(self, manager):
    super(MetricsManager, self).__init__()

    self.__watchers = [
      MetricsAggregator('/opt/lake/metrics', manager),
      MetricsAggregator('/opt/vault/metrics', manager),
      MetricsAggregator('/opt/ledger/metrics', manager),
    ]

  def start(self) -> None:
    for watcher in self.__watchers:
      watcher.start()

  def stop(self) -> None:
    for watcher in self.__watchers:
      watcher.stop()

  def persist(self, label) -> None:
    with open('{0}/{1}.json'.format('/reports/perf_metrics', label), mode='w', encoding="ascii") as f:
      store = {}
      for watcher in self.__watchers:
        store.update(watcher.get_metrics())
      json.dump(store, f, indent=4, sort_keys=True)
