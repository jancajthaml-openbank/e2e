#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from systemd.common import Unit
from helpers.eventually import eventually
from helpers.shell import execute
import string
import time
import os


class VaultRest(Unit):

  def __init__(self):
    (code, result) = execute([
      "systemctl", "start", 'vault-rest'
    ], silent=True)
    assert code == 0, str(result)

  def __repr__(self):
    return 'VaultRest()'

  def teardown(self):
    @eventually(5)
    def eventual_teardown():
      (code, result) = execute([
        'systemctl', 'stop', 'vault-rest'
      ], silent=True)
      assert code == 0, str(result)

    eventual_teardown()

  def restart(self) -> bool:
    @eventually(2)
    def eventual_restart():
      (code, result) = execute([
        "systemctl", "restart", 'vault-rest'
      ], silent=True)
      assert code == 0, str(result)

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

    os.makedirs('/etc/vault/conf.d', exist_ok=True)
    with open('/etc/vault/conf.d/init.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    if not self.restart():
      raise RuntimeError("vault-rest failed to restart")

  @property
  def is_healthy(self) -> bool:
    try:
      @eventually(10)
      def eventual_check():
        (code, result) = execute([
          "systemctl", "show", "-p", "SubState", "vault-rest"
        ], silent=True)
        assert "SubState=running" == str(result).strip(), str(result)
      eventual_check()
    except:
      return False
    return True
