#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from systemd.common import Unit
from metrics.aggregator import MetricsAggregator
from helpers.eventually import eventually
from helpers.shell import execute
import string
import time
import os


class VaultRest(Unit):

  def __init__(self):
    self.__metrics = None

    (code, result) = execute([
      "systemctl", "start", 'vault-rest'
    ])
    assert code == 0, str(result)

    self.watch_metrics()

  def __repr__(self):
    return 'VaultRest()'

  def teardown(self):
    @eventually(5)
    def eventual_teardown():
      (code, result) = execute([
        'journalctl', '-o', 'cat', '-u', 'vault-rest.service', '--no-pager'
      ])
      if code == 0 and result:
        with open('/reports/perf_logs/vault-rest.log', 'w') as f:
          f.write(result)

      (code, result) = execute([
        'systemctl', 'stop', 'vault-rest'
      ])
      assert code == 0, str(result)

      (code, result) = execute([
        'journalctl', '-o', 'cat', '-u', 'vault-rest.service', '--no-pager'
      ])
      if code == 0 and result:
        with open('/reports/perf_logs/vault-rest.log', 'w') as f:
          f.write(result)

    eventual_teardown()

    if self.__metrics:
      self.__metrics.stop()

  def restart(self) -> bool:
    @eventually(2)
    def eventual_restart():
      (code, result) = execute([
        "systemctl", "restart", 'vault-rest'
      ])
      assert code == 0, str(result)

    eventual_restart()

    return self.is_healthy

  def watch_metrics(self) -> None:
    metrics_output = None

    if os.path.exists('/etc/init/vault.conf'):
      with open('/etc/init/vault.conf', 'r') as f:
        for line in f:
          (key, val) = line.rstrip().split('=')
          if key == 'VAULT_METRICS_OUTPUT':
            metrics_output = '{0}/metrics.json'.format(val)
            break

    if metrics_output:
      self.__metrics = MetricsAggregator(metrics_output)
      self.__metrics.start()

  def get_metrics(self) -> None:
    if self.__metrics:
      return self.__metrics.get_metrics()
    return {}

  def reconfigure(self, params) -> None:
    d = {}

    if os.path.exists('/etc/init/vault.conf'):
      with open('/etc/init/vault.conf', 'r') as f:
        for line in f:
          (key, val) = line.rstrip().split('=')
          d[key] = val

    for k, v in params.items():
      key = 'VAULT_{0}'.format(k)
      if key in d:
        d[key] = v

    os.makedirs("/etc/init", exist_ok=True)
    with open('/etc/init/vault.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    if not self.restart():
      raise RuntimeError("vault-rest failed to restart")

  @property
  def is_healthy(self) -> bool:
    def single_check():
      (code, result) = execute([
        "systemctl", "show", "-p", "SubState", "vault-rest"
      ])
      return "SubState=running" == str(result)

    if single_check():
      return True

    @eventually(3)
    def eventual_check():
      assert single_check() is True

    eventual_check()

    return True
