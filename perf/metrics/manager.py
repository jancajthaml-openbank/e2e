#!/usr/bin/env python3

import json

class MetricsManager():

  def __init__(self, manager):
    super(MetricsManager, self).__init__()
    self.__manager = manager

  def persist(self, label) -> None:
    with open('{0}/{1}.json'.format('/reports/perf_metrics', label), mode='w', encoding='ascii') as f:
      store = {}
      for units in self.__manager.values():
        for unit in units:
          store.update(unit.get_metrics())

      json.dump(store, f, indent=4, sort_keys=True)
