#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unit.common import Unit
from helpers.eventually import eventually
from helpers.shell import execute
import string
import time
import os


class LedgerRest(Unit):

  def __init__(self):
    (code, result, error) = execute(["systemctl", "start", 'ledger-rest'])
    assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

  def __repr__(self):
    return 'LedgerRest()'

  def teardown(self):
    @eventually(5)
    def eventual_teardown():
      (code, result, error) = execute(['systemctl', 'stop', 'ledger-rest'])
      assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

    eventual_teardown()

  def restart(self) -> bool:
    @eventually(2)
    def eventual_restart():
      (code, result, error) = execute(["systemctl", "restart", 'ledger-rest'])
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

    self.is_healthy

  @property
  def is_healthy(self) -> bool:
    try:
      @eventually(10)
      def eventual_check():
        (code, result, error) = execute([
          "systemctl", "show", "-p", "SubState", "ledger-rest"
        ])
        assert "SubState=running" == str(result).strip(), code + ' ' + str(result) + ' ' + str(error)
      eventual_check()
    except:
      return False
    return True
