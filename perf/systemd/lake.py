#!/usr/bin/env python

from systemd.common import Unit
import subprocess
import multiprocessing
import string
import requests
import time

class Lake(Unit):

  def __init__(self):
    self.units = []

    self.units.append('lake')

  def teardown(self):
    try:
      subprocess.check_call(["systemctl", "stop", 'lake'], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
      out = subprocess.check_output(["journalctl", "-o", "short-precise", "-u", 'lake'], stderr=subprocess.STDOUT).decode("utf-8").strip()
      with open('/reports/perf_logs/lake.log', 'w') as the_file:
        the_file.write(out)
    except subprocess.CalledProcessError as ex:
      pass
    pass

  def restart(self) -> bool:
    out = None
    try:
      subprocess.check_call(["systemctl", "restart", 'lake'], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
      raise RuntimeError("Failed to restart lake with error {0}".format(ex))
    return self.is_healthy

  @property
  def is_healthy(self) -> bool:
    def single_check():
      all_ok = True

      for unit in self.units:
        out = subprocess.check_output(["systemctl", "show", "-p", "SubState", unit], stderr=subprocess.STDOUT).decode("utf-8").strip()
        all_ok &= (out == "SubState=running")

      return all_ok

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
