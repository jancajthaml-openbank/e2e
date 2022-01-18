#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import tarfile
import tempfile
import errno
import os
import datetime
import subprocess
from helpers.eventually import eventually
from openbank_testkit import Package, Platform, Shell


class ApplianceHelper(object):

  def __init__(self, context):
    self.units = list()
    self.services = {
      "lake": None,
      "vault": None,
      "ledger": None,
      "data-warehouse": None,
    }
    self.context = context

  def setup(self):
    os.makedirs("/etc/data-warehouse/conf.d", exist_ok=True)
    with open('/etc/data-warehouse/conf.d/init.conf', 'w') as fd:
      fd.write(str(os.linesep).join([
        "DATA_WAREHOUSE_LOG_LEVEL=DEBUG",
        "DATA_WAREHOUSE_HTTP_PORT=8080",
        "DATA_WAREHOUSE_POSTGRES_URL=jdbc:postgresql://postgres:5432/openbank",
        "DATA_WAREHOUSE_PRIMARY_STORAGE_PATH=/data"
      ]))

    os.makedirs("/etc/lake/conf.d", exist_ok=True)
    with open('/etc/lake/conf.d/init.conf', 'w') as fd:
      fd.write(str(os.linesep).join([
        "LAKE_LOG_LEVEL=DEBUG",
        "LAKE_PORT_PULL=5562",
        "LAKE_PORT_PUB=5561",
        "LAKE_STATSD_ENDPOINT=127.0.0.1:8125"
      ]))

    os.makedirs("/etc/vault/conf.d", exist_ok=True)
    with open('/etc/vault/conf.d/init.conf', 'w') as fd:
      fd.write(str(os.linesep).join([
        "VAULT_STORAGE=/data",
        "VAULT_LOG_LEVEL=DEBUG",
        "VAULT_SNAPSHOT_SATURATION_TRESHOLD=100",
        "VAULT_HTTP_PORT=4400",
        "VAULT_SERVER_KEY=/etc/vault/secrets/domain.local.key",
        "VAULT_SERVER_CERT=/etc/vault/secrets/domain.local.crt",
        "VAULT_LAKE_HOSTNAME=127.0.0.1",
        "VAULT_MEMORY_THRESHOLD=0",
        "VAULT_STORAGE_THRESHOLD=0",
        "VAULT_STATSD_ENDPOINT=127.0.0.1:8125"
      ]))

    os.makedirs("/etc/ledger/conf.d", exist_ok=True)
    with open('/etc/ledger/conf.d/init.conf', 'w') as fd:
      fd.write(str(os.linesep).join([
        "LEDGER_STORAGE=/data",
        "LEDGER_LOG_LEVEL=DEBUG",
        "LEDGER_HTTP_PORT=4401",
        "LEDGER_SERVER_KEY=/etc/ledger/secrets/domain.local.key",
        "LEDGER_SERVER_CERT=/etc/ledger/secrets/domain.local.crt",
        "LEDGER_LAKE_HOSTNAME=127.0.0.1",
        "LEDGER_TRANSACTION_INTEGRITY_SCANINTERVAL=5m",
        "LEDGER_MEMORY_THRESHOLD=0",
        "LEDGER_STORAGE_THRESHOLD=0",
        "LEDGER_STATSD_ENDPOINT=127.0.0.1:8125"
      ]))

  def download(self):
    for service in self.services.keys():
      package = Package(service)
      version = package.latest_version
      assert version, 'no version known for {}'.format(service)
      self.services[service] = version
      assert package.download(version, 'main', '/tmp/packages'), 'unable to download package {}'.format(service)

  def install(self):
    for service in self.services:
      version = self.services[service]
      (code, result, error) = Shell.run([
        "apt-get", "install", "-f", "-qq", "-o=Dpkg::Use-Pty=0", "-o=Dpkg::Options::=--force-confdef", "-o=Dpkg::Options::=--force-confnew", '/tmp/packages/{}_{}_{}.deb'.format(service, version, Platform.arch)
      ])
      assert code == 'OK', str(code) + ' ' + result

  def running(self):
    (code, result, error) = Shell.run(["systemctl", "list-units", "--no-legend", "--state=active"])
    if code != 'OK':
      return False

    all_running = True
    for unit in self.units:
      if not unit.endswith('.service'):
        continue

      (code, result, error) = Shell.run(["systemctl", "show", "-p", "SubState", unit])

      if unit.endswith('-watcher.service'):
        all_running &= 'SubState=dead' in result
      else:
        all_running &= ('SubState=running' in result or 'SubState=exited' in result)

    return all_running

  def __is_openbank_unit(self, unit):
    for mask in self.services:
      if mask in unit:
        return True
    return False

  def collect_logs(self):
    for unit in set(self.__get_systemd_units() + self.units):
      (code, result, error) = Shell.run(['journalctl', '-o', 'cat', '-u', unit, '--no-pager'])
      if code != 'OK' or not result:
        continue
      with open('reports/blackbox-tests/logs/{}.log'.format(unit), 'w') as fd:
        fd.write(result)

    (code, result, error) = Shell.run(['journalctl', '-o', 'cat', '--no-pager'])
    if code == 'OK':
      with open('reports/blackbox-tests/logs/journal.log', 'w') as fd:
        fd.write(result)

  def __get_systemd_units(self):
    (code, result, error) = Shell.run(['systemctl', 'list-units', '--no-legend', '--state=active'])
    result = [item.strip().split(' ')[0].strip() for item in result.split(os.linesep)]
    result = [item for item in result if not item.endswith('unit.slice')]
    result = [item for item in result if self.__is_openbank_unit(item)]
    return result

  def teardown(self):
    self.collect_logs()
    # INFO patch
    for unit in reversed(sorted(self.__get_systemd_units(), key=len)):
      Shell.run(['systemctl', 'stop', unit])
    self.collect_logs()
