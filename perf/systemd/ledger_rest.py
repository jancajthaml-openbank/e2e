#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from systemd.common import Unit
from metrics.aggregator import MetricsAggregator
from helpers.eventually import eventually
from helpers.shell import execute
import string
import time
import os


class LedgerRest(Unit):

  def __init__(self):
    self.__metrics = None

    (code, result) = execute([
      "systemctl", "start", 'ledger-rest'
    ], silent=True)
    assert code == 0, str(result)

    self.watch_metrics()

  def __repr__(self):
    return 'LedgerRest()'

  def teardown(self):
    @eventually(5)
    def eventual_teardown():
      (code, result) = execute([
        'systemctl', 'stop', 'ledger-rest'
      ], silent=True)
      assert code == 0, str(result)

    eventual_teardown()

    if self.__metrics:
      self.__metrics.stop()

  def restart(self) -> bool:
    @eventually(2)
    def eventual_restart():
      (code, result) = execute([
        "systemctl", "restart", 'ledger-rest'
      ], silent=True)
      assert code == 0, str(result)

    eventual_restart()

    return self.is_healthy

  def watch_metrics(self) -> None:
    metrics_output = None

    if os.path.exists('/etc/ledger/conf.d/init.conf'):
      with open('/etc/ledger/conf.d/init.conf', 'r') as f:
        for line in f:
          (key, val) = line.rstrip().split('=')
          if key == 'LEDGER_METRICS_OUTPUT':
            metrics_output = '{0}/metrics.json'.format(val)
            break

    if metrics_output:
      self.__metrics = MetricsAggregator(metrics_output)
      self.__metrics.start()

  def get_metrics(self) -> None:
    if self.__metrics:
      return self.__metrics.get_metrics()
    return dict()

  def reconfigure(self, params) -> None:
    d = dict()

    if os.path.exists('/etc/ledger/conf.d/init.conf'):
      with open('/etc/ledger/conf.d/init.conf', 'r') as f:
        for line in f:
          (key, val) = line.rstrip().split('=')
          d[key] = val

    for k, v in params.items():
      key = 'LEDGER_{0}'.format(k)
      if key in d:
        d[key] = v

    os.makedirs('/etc/ledger/conf.d', exist_ok=True)
    with open('/etc/ledger/conf.d/init.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    if not self.restart():
      raise RuntimeError("ledger-rest failed to restart")

  @property
  def is_healthy(self) -> bool:
    try:
      @eventually(10)
      def eventual_check():
        (code, result) = execute([
          "systemctl", "show", "-p", "SubState", "ledger-rest"
        ], silent=True)
        assert "SubState=running" == str(result).strip(), str(result)
      eventual_check()
    except:
      return False
    return True
