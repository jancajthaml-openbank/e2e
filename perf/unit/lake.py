#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unit.common import Unit
from helpers.eventually import eventually
from openbank_testkit import Shell
import string
import time
import os


class Lake(Unit):

  def __init__(self):
    (code, result, error) = Shell.run(['systemctl', 'start', 'lake-relay'])
    assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

  def __repr__(self):
    return 'Lake()'

  def teardown(self):
    @eventually(5)
    def eventual_teardown():
      (code, result, error) = Shell.run(['systemctl', 'stop', 'lake-relay'])
      assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

    eventual_teardown()

  def restart(self) -> bool:
    @eventually(2)
    def eventual_restart():
      (code, result, error) = Shell.run(['systemctl', 'restart', 'lake-relay'])
      assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

    eventual_restart()

    return self.is_healthy

  def reconfigure(self, params) -> None:
    d = dict()

    if os.path.exists('/etc/lake/conf.d/init.conf'):
      with open('/etc/lake/conf.d/init.conf', 'r') as f:
        for line in f:
          (key, val) = line.rstrip().split('=')
          d[key] = val

    for k, v in params.items():
      key = 'LAKE_{0}'.format(k)
      if key in d:
        d[key] = v

    os.makedirs('/etc/lake/conf.d', exist_ok=True)
    with open('/etc/lake/conf.d/init.conf', 'w') as f:
      f.write('\n'.join("{!s}={!s}".format(key,val) for (key,val) in d.items()))

    self.is_healthy

  @property
  def is_healthy(self) -> bool:
    try:
      @eventually(10)
      def eventual_check():
        (code, result) = Shell.run([
          "systemctl", "show", "-p", "SubState", "lake-relay"
        ])
        assert "SubState=running" == str(result).strip(), str(result)
      eventual_check()
    except:
      return False
    return True
