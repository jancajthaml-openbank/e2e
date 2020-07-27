#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from systemd.common import Unit
from metrics.aggregator import MetricsAggregator
from helpers.eventually import eventually
from helpers.shell import execute
import string
import time
import os


class VaultUnit(Unit):

  @property
  def tenant(self) -> str:
    return self._tenant

  def __repr__(self):
    return 'VaultUnit({0})'.format(self._tenant)

  def __init__(self, tenant):
    self.__metrics = None
    self._tenant = tenant

    (code, result) = execute([
      "systemctl", "enable", 'vault-unit@{0}'.format(self._tenant)
    ], silent=True)
    assert code == 0, str(result)

    (code, result) = execute([
      "systemctl", "start", 'vault-unit@{0}'.format(self._tenant)
    ], silent=True)
    assert code == 0, str(result)

    self.watch_metrics()

  def teardown(self):
    @eventually(5)
    def eventual_teardown():
      (code, result) = execute([
        'journalctl', '-o', 'cat', '-u', 'vault-unit@{0}.service'.format(self._tenant), '--no-pager'
      ], silent=True)
      if code == 0 and result:
        with open('/reports/perf_logs/vault-unit-{0}.log'.format(self._tenant), 'w') as f:
          f.write(result)

      (code, result) = execute([
        'systemctl', 'stop', 'vault-unit@{0}'.format(self._tenant)
      ], silent=True)
      assert code == 0, str(result)

      (code, result) = execute([
        'journalctl', '-o', 'cat', '-u', 'vault-unit@{0}.service'.format(self._tenant), '--no-pager'
      ], silent=True)
      if code == 0 and result:
        with open('/reports/perf_logs/vault-unit-{0}.log'.format(self._tenant), 'w') as f:
          f.write(result)

    eventual_teardown()

    if self.__metrics:
      self.__metrics.stop()

  def restart(self) -> bool:
    @eventually(2)
    def eventual_restart():
      (code, result) = execute([
        "systemctl", "restart", 'vault-unit@{0}'.format(self._tenant)
      ], silent=True)
      assert code == 0, str(result)

    eventual_restart()

    return self.is_healthy

  def watch_metrics(self) -> None:
    metrics_output = None

    if os.path.exists('/etc/vault/conf.d/init.conf'):
      with open('/etc/vault/conf.d/init.conf', 'r') as f:
        for line in f:
          (key, val) = line.rstrip().split('=')
          if key == 'VAULT_METRICS_OUTPUT':
            metrics_output = '{0}/metrics.{1}.json'.format(val, self._tenant)
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

    if os.path.exists('/etc/vault/conf.d/init.conf'):
      with open('/etc/vault/conf.d/init.conf', 'r') as f:
        for line in f:
          (key, val) = line.rstrip().split('=')
          d[key] = val

    for k, v in params.items():
      key = 'VAULT_{0}'.format(k)
      if key in d:
        d[key] = v

    os.makedirs("/etc/vault/conf.d", exist_ok=True)
    with open('/etc/vault/conf.d/init.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    if not self.restart():
      raise RuntimeError("vault failed to restart")

  @property
  def is_healthy(self) -> bool:
    try:
      @eventually(10)
      def eventual_check():
        (code, result) = execute([
          "systemctl", "show", "-p", "SubState", 'vault-unit@{0}'.format(self._tenant)
        ], silent=True)
        assert "SubState=running" == str(result).strip(), str(result)
      eventual_check()
    except:
      return False
    return True
