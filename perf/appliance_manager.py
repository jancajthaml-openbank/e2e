#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import ssl
try:
  _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
  pass
else:
  ssl._create_default_https_context = _create_unverified_https_context

import docker

from utils import progress, success, debug

from systemd.vault_unit import VaultUnit
from systemd.vault_rest import VaultRest
from systemd.ledger_unit import LedgerUnit
from systemd.ledger_rest import LedgerRest
from systemd.lake import Lake
from helpers.shell import execute

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
    r = self.http.request('GET', uri)
    return r.status == 200

  def get_latest_service_version(self, service):
    headers = {
      'User-Agent': 'https://api.github.com/meta'
    }

    if 'GITHUB_RELEASE_TOKEN' in os.environ:
      headers['Authorization'] = 'token {0}'.format(os.environ['GITHUB_RELEASE_TOKEN'])

    uri = 'https://api.github.com/repos/jancajthaml-openbank/{0}/releases/latest'.format(service)
    r = self.http.request('GET', uri, headers=headers)

    data = r.data.decode('utf-8')

    if r.status != 200:
      raise Exception('GitHUB version fetch failure {0}'.format(data))

    version = json.loads(data)['tag_name']
    if version.startswith('v'):
      version = version[len('v'):]

    return version

  def fetch_versions(self):
    self.http = urllib3.PoolManager()

    for service in ['lake', 'vault', 'ledger']:
      version = self.get_latest_service_version(service)
      self.versions[service] = version

  def get_arch(self):
    return {
      'x86_64': 'amd64',
      'armv7l': 'armhf',
      'armv8': 'arm64'
    }.get(platform.uname().machine, 'amd64')

  def __init__(self):
    self.arch = self.get_arch()

    self.store = dict()
    self.versions = dict()
    self.units = dict()
    self.services = list()
    self.docker = docker.APIClient(base_url='unix://var/run/docker.sock')

    try:
      os.mkdir("/opt/artifacts")
    except OSError as exc:
      if exc.errno != errno.EEXIST:
        raise
      pass

    self.fetch_versions()

    scratch_docker_cmd = ['FROM alpine']
    for service in ['lake', 'vault', 'ledger']:
      version = self.versions[service]
      if self.image_exists('openbank/{0}'.format(service), 'v{0}-master'.format(version)):
        image = 'openbank/{0}:v{1}-master'.format(service, version)
        package = '{0}_{1}+master_{2}'.format(service, version, self.arch)
      else:
        image = 'openbank/{0}:v{1}'.format(service, version)
        package = '{0}_{1}_{2}'.format(service, version, self.arch)

      try:
        self.docker.remove_image(image, force=True)
      except:
        pass
      finally:
        scratch_docker_cmd.append('COPY --from={0} /opt/artifacts/{1}.deb /opt/artifacts/{2}.deb'.format(image, package, service))

    temp = tempfile.NamedTemporaryFile(delete=True)
    try:
      with open(temp.name, 'w') as f:
        for item in scratch_docker_cmd:
          f.write("%s\n" % item)

      for chunk in self.docker.build(fileobj=temp, pull=True, rm=True, decode=True, tag='perf_artifacts-scratch'):
        if 'stream' in chunk:
          for line in chunk['stream'].splitlines():
            if len(line):
              progress('docker {0}'.format(line.strip('\r\n')))

      scratch = self.docker.create_container('perf_artifacts-scratch', '/bin/true')

      if scratch['Warnings']:
        raise Exception(scratch['Warnings'])

      for service in ['lake', 'vault', 'ledger']:
        tar_name = '/opt/artifacts/{0}.tar'.format(service)
        tar_stream, stat = self.docker.get_archive(scratch['Id'], '/opt/artifacts/{0}.deb'.format(service))
        with open(tar_name, 'wb') as destination:
          total_bytes = 0
          for chunk in tar_stream:
            total_bytes += len(chunk)
            progress('extracting {0} {1:.2f}%'.format(stat['name'], min(100, 100 * (total_bytes/stat['size']))))
            destination.write(chunk)
        archive = tarfile.TarFile(tar_name)
        archive.extract('{0}.deb'.format(service), '/opt/artifacts')
        os.remove(tar_name)
        debug('downloaded {0}'.format(stat['name']))

      for service in ['lake', 'vault', 'ledger']:
        (code, result) = execute([
          "dpkg", "-c", "/opt/artifacts/{0}.deb".format(service)
        ])
        assert code == 0, str(result)

      self.docker.remove_container(scratch['Id'])
    finally:
      temp.close()
      self.docker.remove_image('perf_artifacts-scratch', force=True)

    for service in ['lake', 'vault', 'ledger']:
      version = self.versions[service]
      progress('installing {0} {1}'.format(service, version))
      (code, result) = execute([
        "apt-get", "install", "-f", "-qq", "-o=Dpkg::Use-Pty=0", "-o=Dpkg::Options::=--force-confdef", "-o=Dpkg::Options::=--force-confnew", '/tmp/packages/{}.deb'.format(service)
      ])
      assert code == 0, str(result)
      success('installed {0} {1}'.format(service, version))

    (code, result) = execute([
      "systemctl", "-t", "service", "--no-legend"
    ])
    assert code == 0, str(result)

    self.services = set([x.split(' ')[0].split('@')[0].split('.service')[0] for x in installed.splitlines()])

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

  def teardown(self, key=None) -> None:
    if key:
      del self[key]
    else:
      for name in list(self.units):
        del self[name]
