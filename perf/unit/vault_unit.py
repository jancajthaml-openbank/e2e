#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unit.common import Unit
from helpers.eventually import eventually
from helpers.shell import execute
import string
import time
import os


class VaultUnit(Unit):

  @property
  def tenant(self) -> str:
    return self._tenant

  def __repr__(self):
    return 'VaultUnit({0})'.format(self._tenant)

  def __init__(self, tenant):
    self._tenant = tenant

    (code, result, error) = execute([
      "systemctl", "enable", 'vault-unit@{0}'.format(self._tenant)
    ])
    assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

    (code, result, error) = execute([
      "systemctl", "start", 'vault-unit@{0}'.format(self._tenant)
    ])
    assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

  def teardown(self):
    @eventually(5)
    def eventual_teardown():
      (code, result, error) = execute([
        'systemctl', 'stop', 'vault-unit@{0}'.format(self._tenant)
      ])
      assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

    eventual_teardown()

  def restart(self) -> bool:
    @eventually(2)
    def eventual_restart():
      (code, result, error) = execute([
        "systemctl", "restart", 'vault-unit@{0}'.format(self._tenant)
      ])
      assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

    eventual_restart()

    return self.is_healthy

  def reconfigure(self, params) -> None:
    d = dict()

    if os.path.exists('/etc/vault/conf.d/init.conf'):
      with open('/etc/vault/conf.d/init.conf', 'r') as f:
        for line in f:
          (key, val) = line.rstrip().split('=')
          d[key] = val

    for k, v in params.items():
      key = 'VAULT_{0}'.format(k)
      if key in d:
        d[key] = v

    os.makedirs("/etc/vault/conf.d", exist_ok=True)
    with open('/etc/vault/conf.d/init.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    self.is_healthy
    
  @property
  def is_healthy(self) -> bool:
    try:
      @eventually(10)
      def eventual_check():
        (code, result, error) = execute([
          "systemctl", "show", "-p", "SubState", 'vault-unit@{0}'.format(self._tenant)
        ])
        assert "SubState=running" == str(result).strip(), code + ' ' + str(result) + ' ' + str(error)
      eventual_check()
    except:
      return False
    return True
