#!/usr/bin/env python

from systemd.common import Unit
import subprocess
import multiprocessing
import string
import time
import random
secure_random = random.SystemRandom()

class Wall(Unit):

  def __init__(self):
    d = {}

    with open('/etc/init/wall.conf', 'r') as f:
      for line in f:
        (key, val) = line.rstrip().split('=')
        d[key] = val

    self.units = []

    for i in range(int(d['WALL_SCALE'])):
      self.units.append('wall-rest@{0}'.format(i+1))

  def reconfigure(self, params) -> None:
    d = {}

    with open('/etc/init/wall.conf', 'r') as f:
      for line in f:
        (key, val) = line.rstrip().split('=')
        d[key] = val

    for k, v in params.items():
      key = 'WALL_{0}'.format(k)
      if key in d:
        d[key] = v

    with open('/etc/init/wall.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    if not self.restart():
      raise RuntimeError("wall failed to restart")

  def scale(self, size) -> None:
    d = {}

    with open('/etc/init/wall.conf', 'r') as f:
      for line in f:
        (key, val) = line.rstrip().split('=')
        d[key] = val

    d['WALL_SCALE'] = str(size)

    with open('/etc/init/wall.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    self.units = []

    for i in range(size):
      self.units.append('wall-rest@{0}'.format(i+1))

    if not self.restart():
      raise RuntimeError("wall failed to scale")

  def teardown(self):
    def eventual_teardown():
      try:
        out = subprocess.check_output(["journalctl", "-o", "short-precise", "-u", 'wall-scale'], stderr=subprocess.STDOUT).decode("utf-8").strip()
        with open('/reports/perf_logs/wall.log', 'w') as the_file:
          the_file.write(out)
        subprocess.check_call(["systemctl", "stop", 'wall-scale'], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
        out = subprocess.check_output(["journalctl", "-o", "short-precise", "-u", 'wall-scale'], stderr=subprocess.STDOUT).decode("utf-8").strip()
        with open('/reports/perf_logs/wall.log', 'w') as the_file:
          the_file.write(out)
      except subprocess.CalledProcessError as ex:
        pass

    action_process = multiprocessing.Process(target=eventual_teardown)
    action_process.start()
    action_process.join(timeout=5)
    action_process.terminate()

  def restart(self) -> bool:
    out = None
    try:
      subprocess.check_call(["systemctl", "restart", 'wall-scale'], stdout=Unit.FNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
      raise RuntimeError("Failed to restart wall with error {0}".format(ex))
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
