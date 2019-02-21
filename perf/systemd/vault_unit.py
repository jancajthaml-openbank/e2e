#!/usr/bin/env python

from systemd.common import Unit
import subprocess
import multiprocessing
import string
import time
import random
secure_random = random.SystemRandom()

class VaultUnit(Unit):

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
    def eventual_teardown():
      try:
        out = subprocess.check_output(["journalctl", "-o", "short-precise", "-u", 'vault@{0}'.format(self._tenant)], stderr=subprocess.STDOUT).decode("utf-8").strip()
        with open('/reports/perf_logs/vault_{0}.log'.format(self._tenant), 'w') as the_file:
          the_file.write(out)
        subprocess.check_call(["systemctl", "stop", 'vault@{0}'.format(self._tenant)], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
        out = subprocess.check_output(["journalctl", "-o", "short-precise", "-u", 'vault@{0}'.format(self._tenant)], stderr=subprocess.STDOUT).decode("utf-8").strip()
        with open('/reports/perf_logs/vault_{0}.log'.format(self._tenant), 'w') as the_file:
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
        subprocess.check_call(["systemctl", "restart", 'vault@{0}'.format(self._tenant)], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        raise RuntimeError("Failed to restart vault@{0} with error {1}".format(self._tenant, ex))

    action_process = multiprocessing.Process(target=eventual_restart)
    action_process.start()
    action_process.join(timeout=2)
    action_process.terminate()

    return self.is_healthy

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
      raise RuntimeError("vault failed to restart")

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
