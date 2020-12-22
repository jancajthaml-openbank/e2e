#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from systemd.common import Unit
from helpers.eventually import eventually
from helpers.shell import execute
import string
import time
import os


class LedgerUnit(Unit):

  @property
  def tenant(self) -> str:
    return self._tenant

  def __repr__(self):
    return 'LedgerUnit({0})'.format(self._tenant)

  def __init__(self, tenant):
    self._tenant = tenant

    (code, result) = execute([
      "systemctl", "enable", 'ledger-unit@{0}'.format(self._tenant)
    ], silent=True)
    assert code == 0, str(result)

    (code, result) = execute([
      "systemctl", "start", 'ledger-unit@{0}'.format(self._tenant)
    ], silent=True)
    assert code == 0, str(result)

  def teardown(self):
    @eventually(5)
    def eventual_teardown():
      (code, result) = execute([
        'systemctl', 'stop', 'ledger-unit@{0}'.format(self._tenant)
      ], silent=True)
      assert code == 0, str(result)

    eventual_teardown()

  def restart(self) -> bool:
    @eventually(2)
    def eventual_restart():
      (code, result) = execute([
        "systemctl", "restart", 'ledger-unit@{0}'.format(self._tenant)
      ], silent=True)
      assert code == 0, str(result)

    eventual_restart()

    return self.is_healthy

  def reconfigure(self, params) -> None:
    d = dict()

    if os.path.exists('/etc/ledger/conf.d/init.conf'):
      with open('/etc/ledger/conf.d/init.conf', 'r') as f:
        for line in f:
          (key, val) = line.rstrip().split('=')
          d[key] = val

    for k, v in params.items():
      key = 'LEDGER_{0}'.format(k)
      if key in d:
        d[key] = v

    os.makedirs('/etc/ledger/conf.d', exist_ok=True)
    with open('/etc/ledger/conf.d/init.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    if not self.restart():
      raise RuntimeError("ledger failed to restart")

  @property
  def is_healthy(self) -> bool:
    try:
      @eventually(10)
      def eventual_check():
        (code, result) = execute([
          "systemctl", "show", "-p", "SubState", 'ledger-unit@{0}'.format(self._tenant)
        ], silent=True)
        assert "SubState=running" == str(result).strip(), str(result)
      eventual_check()
    except:
      return False
    return True
