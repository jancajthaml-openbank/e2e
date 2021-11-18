#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from utils import progress, success, debug, TTY

from unit.vault_unit import VaultUnit
from unit.vault_rest import VaultRest
from unit.ledger_unit import LedgerUnit
from unit.ledger_rest import LedgerRest
from unit.lake import Lake
from helpers.shell import execute
from helpers.eventually import eventually
from helpers.http import Request

import datetime
import docker
import platform
import tarfile
import tempfile
import errno
import os
import json
import string
import random

secure_random = random.SystemRandom()


class ApplianceManager(object):

  def image_exists(self, image, tag):
    uri = 'https://index.docker.io/v1/repositories/{0}/tags/{1}'.format(image, tag)
    r = Request(method='GET', url=uri)
    return r.do().status == 200

  def get_latest_service_docker_hub_version(self, service):
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
      return None

    parts = latest.get('id', '').split('-')
    version = parts[0] or None

    if version and version.startswith('v'):
      version = version[1:]

    if version.startswith('v'):
      version = version[len('v'):]

    return version

  def get_latest_service_github_version(self, service):
    uri = 'https://api.github.com/repos/jancajthaml-openbank/{0}/releases/latest'.format(service)

    r = Request(method='GET', url=uri)

    if 'GITHUB_RELEASE_TOKEN' in os.environ and os.environ['GITHUB_RELEASE_TOKEN'].strip():
      r.add_header('Authorization', 'token {0}'.format(os.environ['GITHUB_RELEASE_TOKEN'].strip()))
      r.add_header('User-Agent', 'https://api.github.com/meta')
    else:
      r.add_header('User-Agent', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36')

    data = r.read().decode('utf-8')

    if r.status != 200:
      raise Exception('GitHUB version fetch failure {0}'.format(data))

    version = json.loads(data)['tag_name']
    if version.startswith('v'):
      version = version[len('v'):]

    return version

  def get_latest_service_version(self, service):
    version = None
    exceptions = list()

    try:
      return self.get_latest_service_github_version(service)
    except Exception as ex:
      exceptions.append(str(ex))

    try:
      return self.get_latest_service_docker_hub_version(service)
    except Exception as ex:
      exceptions.append(str(ex))

    raise Exception(str(os.linesep).join(exceptions))

  def fetch_versions(self):
    for service in ['lake', 'vault', 'ledger']:
      version = self.get_latest_service_version(service)
      self.versions[service] = version

  def get_arch(self):
    return {
      'x86_64': 'amd64',
      'armv8': 'arm64',
      'aarch64': 'arm64'
    }.get(platform.uname().machine, 'amd64')

  def __init__(self):
    self.arch = self.get_arch()
    self.store = dict()
    self.versions = dict()
    self.units = dict()
    self.services = list()
    self.docker = docker.from_env()

  def setup(self):
    os.makedirs('/tmp/packages', exist_ok=True)

    self.fetch_versions()

    failure = None
    scratch_docker_cmd = ['FROM alpine']
    for service in ['lake', 'vault', 'ledger']:
      version = self.versions[service]
      if self.image_exists('openbank/{}'.format(service), 'v{}-main'.format(version)):
        image = 'docker.io/openbank/{}:v{}-main'.format(service, version)
      else:
        image = 'docker.io/openbank/{}:v{}'.format(service, version)

      package = '{}_{}_{}'.format(service, version, self.arch)

      scratch_docker_cmd.append('COPY --from={0} /opt/artifacts/{1}.deb /tmp/packages/{2}.deb'.format(image, package, service))

    temp = tempfile.NamedTemporaryFile(delete=True)

    try:
      with open(temp.name, 'w') as fd:
        fd.write(str(os.linesep).join(scratch_docker_cmd))

      image, stream = self.docker.images.build(fileobj=temp, rm=True, pull=True, tag='perf_artifacts-scratch')

      if TTY:
        for chunk in stream:
          if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
              if len(line):
                progress('docker {0}'.format(line.rstrip()))

      scratch = self.docker.containers.run('perf_artifacts-scratch', ['/bin/true'], detach=True)

      for service in ['lake', 'vault', 'ledger']:
        tar_name = '/tmp/packages/{}.tar'.format(service)
        bits, stat = scratch.get_archive('/tmp/packages/{}.deb'.format(service))

        if TTY:
          with open(tar_name, 'wb') as fd:
            total_bytes = 0
            for chunk in bits:
              total_bytes += len(chunk)
              progress('extracting {0} {1:.2f}%'.format(stat['name'], min(100, 100 * (total_bytes/stat['size']))))
              fd.write(chunk)
        else:
          progress('extracting {}'.format(stat['name']))
          with open(tar_name, 'wb') as fd:
            for chunk in bits:
              fd.write(chunk)

        archive = tarfile.TarFile(tar_name)
        archive.extract('{}.deb'.format(service), '/tmp/packages')
        os.remove(tar_name)

        debug('downloaded {}'.format(stat['name']))

      scratch.remove()
    except Exception as ex:
      failure = ex
    finally:
      temp.close()
      try:
        self.docker.images.remove('perf_artifacts-scratch', force=True)
      except:
        pass

    if failure:
      raise failure

    for service in ['lake', 'vault', 'ledger']:
      version = self.versions[service]
      progress('installing {} {}'.format(service, version))
      (code, result, error) = execute([
        "apt-get", "install", "-f", "-qq", "-o=Dpkg::Use-Pty=0", "-o=Dpkg::Options::=--force-confdef", "-o=Dpkg::Options::=--force-confnew", '/tmp/packages/{}.deb'.format(service)
      ])
      assert code == 'OK', code + ' ' + str(result) + ' ' + str(error)
      success('installed {} {}'.format(service, version))

    (code, result, error) = execute(["systemctl", "list-units", "--no-legend"])
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
    (code, result, error) = execute(['journalctl', '-o', 'cat', '--no-pager'])
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

