#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unit.common import Unit
from helpers.eventually import eventually
from openbank_testkit import Shell
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

    (code, result, error) = Shell.run([
      "systemctl", "enable", 'ledger-unit@{0}'.format(self._tenant)
    ])
    assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

    (code, result, error) = Shell.run([
      "systemctl", "start", 'ledger-unit@{0}'.format(self._tenant)
    ])
    assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

  def teardown(self):
    @eventually(5)
    def eventual_teardown():
      (code, result, error) = Shell.run([
        'systemctl', 'stop', 'ledger-unit@{0}'.format(self._tenant)
      ])
      assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

    eventual_teardown()

  def restart(self) -> bool:
    @eventually(2)
    def eventual_restart():
      (code, result, error) = Shell.run([
        "systemctl", "restart", 'ledger-unit@{0}'.format(self._tenant)
      ])
      assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

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
        (code, result, error) = Shell.run([
          "systemctl", "show", "-p", "SubState", 'ledger-unit@{0}'.format(self._tenant)
        ])
        assert "SubState=running" == str(result).strip(), code + ' ' + str(result) + ' ' + str(error)
      eventual_check()
    except:
      return False
    return True
