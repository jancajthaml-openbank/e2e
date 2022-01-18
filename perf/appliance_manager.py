#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from utils import progress, success, debug, TTY

from unit.vault_unit import VaultUnit
from unit.vault_rest import VaultRest
from unit.ledger_unit import LedgerUnit
from unit.ledger_rest import LedgerRest
from unit.lake import Lake
from helpers.eventually import eventually
from openbank_testkit import Request, Shell, Package, Platform

import functools
import datetime
import tarfile
import tempfile
import errno
import os
import json
import string
import random

secure_random = random.SystemRandom()


class ApplianceManager(object):

  def __init__(self):
    self.store = dict()
    self.versions = dict()
    self.units = dict()
    self.services = list()

  def setup(self):
    os.makedirs('/tmp/packages', exist_ok=True)

    for service in ['lake', 'vault', 'ledger']:
      progress('fetching version of {}'.format(service))
      package = Package(service)
      version = package.latest_version
      assert version, 'no version known for {}'.format(service)
      self.versions[service] = version
      progress('downloading packages from {} {}'.format(service, version))
      assert package.download(version, 'main', '/tmp/packages'), 'unable to download package {}'.format(service)
      success('downloaded {}_{}_{}.deb'.format(service, version, Platform.arch))

    for service in ['lake', 'vault', 'ledger']:
      version = self.versions[service]
      progress('installing {} {}'.format(service, version))
      (code, result, error) = Shell.run([
        "apt-get", "install", "-f", "-qq", "-o=Dpkg::Use-Pty=0", "-o=Dpkg::Options::=--force-confdef", "-o=Dpkg::Options::=--force-confnew", '/tmp/packages/{}_{}_{}.deb'.format(service, version, Platform.arch)
      ])
      assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)
      success('installed {} {}'.format(service, version))

    (code, result, error) = Shell.run(["systemctl", "list-units", "--no-legend"])
    assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)

    self.services = set([x.split(' ')[0].split('@')[0].split('.service')[0] for x in result.splitlines()])

  def __len__(self):
    return sum([len(x) for x in self.units.values()])

  def __getitem__(self, key):
    return self.units.get(str(key), [])

  def __setitem__(self, key, value):
    self.units.setdefault(str(key), []).append(value)

  def __delitem__(self, key):
    # fixme add lock here
    if not str(key) in self.units:
      return

    for node in self.units[str(key)]:
      node.teardown()

    del self.units[str(key)]

  # fixme __iter__
  def items(self) -> list:
    return self.units.items()

  def values(self) -> list:
    return self.units.values()

  def onboard(self, tenant=None) -> None:
    if not tenant:
      tenant = ''.join(secure_random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    self['vault-unit'] = VaultUnit(tenant)
    self['ledger-unit'] = LedgerUnit(tenant)

  def reconfigure(self, params, key=None) -> None:
    if not key:
      for name in list(self.units):
        for node in self[name]:
          node.reconfigure(params)
      return

    for node in self[key]:
      node.reconfigure(params)

  def restart(self, key=None) -> None:
    if not key:
      for name in list(self.units):
        for node in self[name]:
          node.restart()
      return

    for node in self[key]:
      node.restart()

  def bootstrap(self) -> None:
    if 'lake' in self.services and not self['lake']:
      self['lake'] = Lake()

    if 'vault' in self.services and not self['vault-rest']:
      self['vault-rest'] = VaultRest()

    if 'ledger' in self.services and not self['ledger-rest']:
      self['ledger-rest'] = LedgerRest()

  def teardown(self) -> None:
    for name in reversed(sorted(list(self.units), key=len)):
      del self[name]

    self.collect_logs()

  def collect_logs(self):
    (code, result, error) = Shell.run(['journalctl', '-o', 'cat', '--no-pager'])
    if code == 'OK':
      with open('reports/perf-tests/logs/journal.log', 'w') as fd:
        fd.write(result)

  @property
  def is_healthy(self) -> bool:
    try:
      vault_requert = Request(method='GET', url='https://127.0.0.1:4400/health')
      ledger_requert = Request(method='GET', url='https://127.0.0.1:4401/health')

      @eventually(10)
      def vault_rest_healthy():
        assert vault_requert.do().status == 200

      @eventually(10)
      def ledger_rest_healthy():
        assert ledger_requert.do().status == 200

      vault_rest_healthy()
      ledger_rest_healthy()
    except Exception as ex:
      print('error {}'.format(ex))
      return False
    return True

