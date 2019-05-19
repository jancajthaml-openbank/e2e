#!/usr/bin/env python

from systemd.common import Unit
from metrics.aggregator import MetricsAggregator
import subprocess
import multiprocessing
import string
import time

class VaultRest(Unit):

  def __init__(self):
    self.__metrics = None

    try:
      subprocess.check_call(["systemctl", "start", 'vault-rest'], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
      raise RuntimeError("Failed to onboard 'vault-rest' with error {0}".format(ex))

    self.watch_metrics()

  def __repr__(self):
    return 'VaultRest()'

  def teardown(self):
    def eventual_teardown():
      try:
        out = subprocess.check_output(["journalctl", "-o", "short-precise", "-u", 'vault-rest'], stderr=subprocess.STDOUT).decode("utf-8").strip()
        with open('/reports/perf_logs/ledger-rest.log', 'w') as the_file:
          the_file.write(out)
        subprocess.check_call(["systemctl", "stop", "vault-rest"], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
        out = subprocess.check_output(["journalctl", "-o", "short-precise", "-u", "vault-rest"], stderr=subprocess.STDOUT).decode("utf-8").strip()
        with open('/reports/perf_logs/vault-rest.log', 'w') as the_file:
          the_file.write(out)
      except subprocess.CalledProcessError as ex:
        pass

    action_process = multiprocessing.Process(target=eventual_teardown)
    action_process.start()
    action_process.join(timeout=5)
    action_process.terminate()

    if self.__metrics:
      self.__metrics.stop()

  def restart(self) -> bool:
    def eventual_restart():
      try:
        subprocess.check_call(["systemctl", "restart", "vault-rest"], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        raise RuntimeError("Failed to restart vault-rest with error {0}".format(ex))

    action_process = multiprocessing.Process(target=eventual_restart)
    action_process.start()
    action_process.join(timeout=2)
    action_process.terminate()

    return self.is_healthy

  def watch_metrics(self) -> None:
    metrics_output = None
    with open('/etc/init/vault.conf', 'r') as f:
      for line in f:
        (key, val) = line.rstrip().split('=')
        if key == 'VAULT_METRICS_OUTPUT':
          metrics_output = val
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

    with open('/etc/init/vault.conf', 'r') as f:
      for line in f:
        (key, val) = line.rstrip().split('=')
        d[key] = val

    for k, v in params.items():
      key = 'VAULT_{0}'.format(k)
      if key in d:
        d[key] = v

    with open('/etc/init/vault.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    if not self.restart():
      raise RuntimeError("vault-rest failed to restart")

  @property
  def is_healthy(self) -> bool:
    def single_check():
      out = subprocess.check_output(["systemctl", "show", "-p", "SubState", "vault-rest"], stderr=subprocess.STDOUT).decode("utf-8").strip()
      return out == "SubState=running"

    if single_check():
      return True

    def eventual_check():
      while True:
        if single_check():
          exit(0)
        time.sleep(0.1)

    action_process = multiprocessing.Process(target=eventual_check)
    action_process.start()
    action_process.join(timeout=3)
    action_process.terminate()

    return action_process.exitcode == 0
