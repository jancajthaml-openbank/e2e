#!/usr/bin/env python

from systemd.common import Unit
import subprocess
import multiprocessing
import string
import time

class Lake(Unit):

  def __init__(self):
    self.units = []

    self.units.append('lake-relay')

  def teardown(self):
    def eventual_teardown():
      try:
        out = subprocess.check_output(["journalctl", "-o", "short-precise", "-u", 'lake-relay'], stderr=subprocess.STDOUT).decode("utf-8").strip()
        with open('/reports/perf_logs/lake.log', 'w') as the_file:
          the_file.write(out)
        subprocess.check_call(["systemctl", "stop", 'lake-relay'], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
        out = subprocess.check_output(["journalctl", "-o", "short-precise", "-u", 'lake-relay'], stderr=subprocess.STDOUT).decode("utf-8").strip()
        with open('/reports/perf_logs/lake.log', 'w') as the_file:
          the_file.write(out)
      except subprocess.CalledProcessError as ex:
        pass

    action_process = multiprocessing.Process(target=eventual_teardown)
    action_process.start()
    action_process.join(timeout=5)
    action_process.terminate()

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

  def reconfigure(self, params) -> None:
    d = {}

    with open('/etc/init/lake.conf', 'r') as f:
      for line in f:
        (key, val) = line.rstrip().split('=')
        d[key] = val

    for k, v in params.items():
      key = 'LAKE_{0}'.format(k)
      if key in d:
        d[key] = v

    with open('/etc/init/lake.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    if not self.restart():
      raise RuntimeError("lake failed to restart")

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
