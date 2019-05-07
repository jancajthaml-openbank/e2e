#!/usr/bin/env python
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

import platform
import tarfile
import tempfile
import errno
import os
import json
import subprocess
import string
import random
secure_random = random.SystemRandom()

class ApplianceManager(object):

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

    del self.http

  def get_arch(self):
    return {
      'x86_64': 'amd64',
      'armv7l': 'armhf',
      'armv8': 'arm64'
    }.get(platform.uname().machine, 'amd64')

  def __init__(self):
    self.arch = self.get_arch()

    self.store = {}
    self.versions = {}
    self.units = {}
    self.docker = docker.APIClient(base_url='unix://var/run/docker.sock')

    DEVNULL = open(os.devnull, 'w')

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
      scratch_docker_cmd.append('COPY --from=openbank/{0}:v{1}-master /opt/artifacts/{0}_{1}+master_{2}.deb /opt/artifacts/{0}.deb'.format(service, version, self.arch))

    temp = tempfile.NamedTemporaryFile(delete=True)
    try:
      with open(temp.name, 'w') as f:
        for item in scratch_docker_cmd:
          f.write("%s\n" % item)

      for chunk in self.docker.build(fileobj=temp, rm=True, decode=True, tag='perf_artifacts-scratch'):
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

      self.docker.remove_container(scratch['Id'])
    finally:
      temp.close()
      self.docker.remove_image('perf_artifacts-scratch', force=True)

    for service in ['lake', 'vault', 'ledger']:
      version = self.versions[service]
      progress('installing {0} {1}'.format(service, version))
      subprocess.check_call(["apt-get", "-y", "install", "-f", "-qq", "-o=Dpkg::Use-Pty=0", '/opt/artifacts/{0}.deb'.format(service)], stdout=DEVNULL, stderr=subprocess.STDOUT)
      success('installed {0} {1}'.format(service, version))

    DEVNULL.close()

    installed = subprocess.check_output(["systemctl", "-t", "service", "--no-legend"], stderr=subprocess.STDOUT).decode("utf-8").strip()
    services = set([x.split(' ')[0].split('@')[0].split('.service')[0] for x in installed.splitlines()])

    if 'lake' in services:
      self['lake'] = Lake()

    if 'vault' in services:
      self['vault-rest'] = VaultRest()

    if 'ledger' in services:
      self['ledger-rest'] = LedgerRest()

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

  def reset(self, key=None) -> None:
    if not key:
      for name in list(self.units):
        for node in self[name]:
          node.restart()
      return

    for node in self[key]:
      node.restart()

  def teardown(self, key=None) -> None:
    if key:
      del self[key]
    else:
      for name in list(self.units):
        del self[name]
