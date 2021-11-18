#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import docker
import urllib.request
import platform
import tarfile
import tempfile
import errno
import os
import json
import datetime
import subprocess
from .shell import execute
from .http import Request


class ApplianceHelper(object):

  def get_arch(self):
    return {
      'x86_64': 'amd64',
      'armv7l': 'armhf',
      'armv8': 'arm64',
      'aarch64': 'arm64'
    }.get(platform.uname().machine, 'amd64')

  def __init__(self, context):
    self.arch = self.get_arch()
    self.units = list()
    self.services = [
      "lake",
      "vault",
      "ledger",
      "data-warehouse",
    ]
    self.docker = docker.from_env()
    self.context = context

  def get_latest_version(self, service):
    uri = "https://hub.docker.com/v2/repositories/openbank/{}/tags/".format(service)

    request = Request(method='GET', url=uri)
    request.add_header('Accept', 'application/json')
    response = request.do()

    if not response.status == 200:
      return None

    body = json.loads(response.read().decode('utf-8')).get('results', [])
    tags = []

    for entry in body:
      tags.append({
        'ts': datetime.datetime.strptime(entry['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ"),
        'id': entry['name'],
      })

    latest = max(tags, key=lambda x: x['ts'])
    if not latest:
      return (None, None)

    parts = latest.get('id', '').split('-')
    version = parts[0] or None

    if len(parts) > 1:
      meta = 'main'
    else:
      meta = None

    if version and version.startswith('v'):
      version = version[1:]

    return (version, meta)

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
    failure = None
    os.makedirs('/tmp/packages', exist_ok=True)

    scratch_docker_cmd = ['FROM alpine']

    for service in self.services:
      version, meta = self.get_latest_version(service)
      assert version, 'missing version for {}'.format(service)

      image = 'docker.io/openbank/{}:v{}'.format(service, (version+'-'+meta) if meta else version)
      package = '/opt/artifacts/{}_{}_{}.deb'.format(service, version, self.arch)
      target = '/tmp/packages/{}.deb'.format(service)

      scratch_docker_cmd.append('COPY --from={} {} {}'.format(image, package, target))

    temp = tempfile.NamedTemporaryFile(delete=True)
    try:
      with open(temp.name, 'w') as fd:
        fd.write(str(os.linesep).join(scratch_docker_cmd))

      image, stream = self.docker.images.build(fileobj=temp, rm=True, pull=True, tag='bbtest_artifacts-scratch')
      for chunk in stream:
        if not 'stream' in chunk:
          continue
        for line in chunk['stream'].splitlines():
          l = line.strip(os.linesep)
          if not len(l):
            continue
          print(l)

      scratch = self.docker.containers.run('bbtest_artifacts-scratch', ['/bin/true'], detach=True)

      tar_name = tempfile.NamedTemporaryFile(delete=True)

      for service in self.services:
        bits, stat = scratch.get_archive('/tmp/packages/{}.deb'.format(service))
        with open(tar_name.name, 'wb') as fd:
          for chunk in bits:
            fd.write(chunk)

        archive = tarfile.TarFile(tar_name.name)
        archive.extract('{}.deb'.format(service), '/tmp/packages')

        (code, result, error) = execute(['dpkg', '-c', '/tmp/packages/{}.deb'.format(service)])
        assert code == 'OK', str(code) + ' ' + result

        with open('reports/blackbox-tests/meta/debian.{}.txt'.format(service), 'w') as fd:
          fd.write(result)

        result = [item for item in result.split(os.linesep)]
        result = [item.rsplit('/', 1)[-1].strip() for item in result if "/lib/systemd/system/{}".format(service) in item]
        result = [item for item in result if not item.endswith('@.service')]

        self.units += result

      scratch.remove()
    except Exception as ex:
      failure = ex
    finally:
      temp.close()
      try:
        self.docker.images.remove('bbtest_artifacts-scratch', force=True)
      except:
        pass

    if failure:
      raise failure

  def install(self):
    for service in self.services:
      (code, result, error) = execute([
        "apt-get", "install", "-f", "-qq", "-o=Dpkg::Use-Pty=0", "-o=Dpkg::Options::=--force-confdef", "-o=Dpkg::Options::=--force-confnew", '/tmp/packages/{}.deb'.format(service)
      ])
      assert code == 'OK', str(code) + ' ' + result

  def running(self):
    (code, result, error) = execute(["systemctl", "list-units", "--no-legend", "--state=active"])
    if code != 'OK':
      return False

    all_running = True
    for unit in self.units:
      if not unit.endswith('.service'):
        continue

      (code, result, error) = execute(["systemctl", "show", "-p", "SubState", unit])

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
      (code, result, error) = execute(['journalctl', '-o', 'cat', '-u', unit, '--no-pager'])
      if code != 'OK' or not result:
        continue
      with open('reports/blackbox-tests/logs/{}.log'.format(unit), 'w') as fd:
        fd.write(result)

    (code, result, error) = execute(['journalctl', '-o', 'cat', '--no-pager'])
    if code == 'OK':
      with open('reports/blackbox-tests/logs/journal.log', 'w') as fd:
        fd.write(result)

  def __get_systemd_units(self):
    (code, result, error) = execute(['systemctl', 'list-units', '--no-legend', '--state=active'])
    result = [item.split(' ')[0].strip() for item in result.split(os.linesep)]
    result = [item for item in result if not item.endswith('unit.slice')]
    result = [item for item in result if self.__is_openbank_unit(item)]
    return result

  def teardown(self):
    self.collect_logs()
    # INFO patch
    for unit in reversed(sorted(self.__get_systemd_units(), key=len)):
      execute(['systemctl', 'stop', unit])
    self.collect_logs()
