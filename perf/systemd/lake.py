#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from systemd.common import Unit
from metrics.aggregator import MetricsAggregator
import subprocess
import multiprocessing
import string
import time
import os


class Lake(Unit):

  def __init__(self):
    self.__metrics = None

    try:
      subprocess.check_call(["systemctl", "start", 'lake'], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
      raise RuntimeError("Failed to onboard 'lake' with error {0}".format(ex))

    self.watch_metrics()

  def __repr__(self):
    return 'Lake()'

  def teardown(self):
    def eventual_teardown():
      try:
        out = subprocess.check_output(['journalctl', '-o', 'cat', '-t', 'lake', '-u', 'lake-relay.service'], stderr=subprocess.STDOUT).decode("utf-8").strip()
        with open('/reports/perf_logs/lake.log', 'w') as the_file:
          the_file.write(out)
        subprocess.check_call(["systemctl", "stop", 'lake-relay'], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
        out = subprocess.check_output(['journalctl', '-o', 'cat', '-t', 'lake', '-u', 'lake-relay.service'], stderr=subprocess.STDOUT).decode("utf-8").strip()
        with open('/reports/perf_logs/lake.log', 'w') as the_file:
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
        subprocess.check_call(["systemctl", "restart", "lake-relay"], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        raise RuntimeError("Failed to restart lake-relay with error {0}".format(ex))

    action_process = multiprocessing.Process(target=eventual_restart)
    action_process.start()
    action_process.join(timeout=2)
    action_process.terminate()

    return self.is_healthy

  def watch_metrics(self) -> None:
    metrics_output = None
    with open('/etc/init/lake.conf', 'r') as f:
      for line in f:
        (key, val) = line.rstrip().split('=')
        if key == 'LAKE_METRICS_OUTPUT':
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

    if os.path.exists('/etc/init/lake.conf'):
      with open('/etc/init/lake.conf', 'r') as f:
        for line in f:
          (key, val) = line.rstrip().split('=')
          d[key] = val

    for k, v in params.items():
      key = 'LAKE_{0}'.format(k)
      if key in d:
        d[key] = v

    os.makedirs("/etc/init", exist_ok=True)
    with open('/etc/init/lake.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    if not self.restart():
      raise RuntimeError("lake failed to restart")

  @property
  def is_healthy(self) -> bool:
    def single_check():
      out = subprocess.check_output(["systemctl", "show", "-p", "SubState", "lake-relay"], stderr=subprocess.STDOUT).decode("utf-8").strip()
      return (out == "SubState=running")

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

    if action_process.exitcode != 0:
      return False

    # fixme http ping now

    return True
