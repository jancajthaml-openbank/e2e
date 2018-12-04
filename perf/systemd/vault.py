#!/usr/bin/env python

from systemd.common import Unit
import subprocess
import multiprocessing
import string
import time
import random
secure_random = random.SystemRandom()

class Vault(Unit):

  @property
  def tenant(self) -> str:
    return self._tenant

  def __init__(self, tenant):
    self._tenant = tenant
    try:
      subprocess.check_call(["systemctl", "enable", 'vault@{0}'.format(self._tenant)], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
      subprocess.check_call(["systemctl", "start", 'vault@{0}'.format(self._tenant)], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
      raise RuntimeError("Failed to onboard vault@{0} with error {1}".format(self._tenant, ex))

  def teardown(self):
    try:
      subprocess.check_call(["systemctl", "stop", 'vault@{0}'.format(self._tenant)], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
      out = subprocess.check_output(["journalctl", "-o", "short-precise", "-u", 'vault@{0}'.format(self._tenant)], stderr=subprocess.STDOUT).decode("utf-8").strip()
      with open('/reports/perf_logs/vault_{0}.log'.format(self._tenant), 'w') as the_file:
        the_file.write(out)
    except subprocess.CalledProcessError as ex:
      pass
    pass

  def restart(self) -> bool:
    try:
      subprocess.check_call(["systemctl", "restart", 'vault@{0}'.format(self._tenant)], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
      raise RuntimeError("Failed to restart vault@{0} with error {1}".format(self._tenant, ex))
    return self.is_healthy

  @property
  def is_healthy(self) -> bool:
    def single_check():
      out = subprocess.check_output(["systemctl", "show", "-p", "SubState", 'vault@{0}'.format(self._tenant)], stderr=subprocess.STDOUT).decode("utf-8").strip()
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
