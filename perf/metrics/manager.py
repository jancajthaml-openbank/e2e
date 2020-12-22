#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from metrics.aggregator import MetricsAggregator


class MetricsManager():

  def __init__(self):
    super(MetricsManager, self).__init__()
    self.__metrics = MetricsAggregator('openbank')

  def start(self):
    self.__metrics.start()

  def stop(self):
    self.__metrics.stop()

  def persist(self, label) -> None:
    with open('reports/perf-tests/metrics/{}.json'.format(label), mode='w', encoding='ascii') as fd:
      store = self.__metrics.get_metrics()
      self.__metrics.clear()
      json.dump(store, fd, indent=4, sort_keys=True)
