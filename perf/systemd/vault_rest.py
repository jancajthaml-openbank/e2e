#!/usr/bin/env python

from systemd.common import Unit
import subprocess
import multiprocessing
import string
import time
import random
secure_random = random.SystemRandom()

class VaultRest(Unit):

  def teardown(self):
    def eventual_teardown():
      try:
        subprocess.check_call(["systemctl", "stop", "vault"], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
        out = subprocess.check_output(["journalctl", "-o", "short-precise", "-u", "vault"], stderr=subprocess.STDOUT).decode("utf-8").strip()
        with open('/reports/perf_logs/vault.log', 'w') as the_file:
          the_file.write(out)
      except subprocess.CalledProcessError as ex:
        pass

    action_process = multiprocessing.Process(target=eventual_teardown)
    action_process.start()
    action_process.join(timeout=5)
    action_process.terminate()

  def restart(self) -> bool:
    try:
      subprocess.check_call(["systemctl", "restart", "vault"], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
      raise RuntimeError("Failed to restart vault with error {0}".format(ex))
    return self.is_healthy

  def reconfigure(self, params) -> None:
    d = {}

    with open('/etc/init/vault.conf', 'r') as f:
      for line in f:
        (key, val) = line.rstrip().split('=')
        d[key] = val

    for k, v in params.items():
      d['VAULT_{0}'.format(k)] = v

    with open('/etc/init/vault.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    if not self.restart():
      raise RuntimeError("vault failed to restart")

  @property
  def is_healthy(self) -> bool:
    def single_check():
      out = subprocess.check_output(["systemctl", "show", "-p", "SubState", "vault"], stderr=subprocess.STDOUT).decode("utf-8").strip()
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
