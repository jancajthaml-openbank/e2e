#!/usr/bin/env python

import docker

from utils import progress, debug

from systemd.vault_unit import VaultUnit
from systemd.vault_rest import VaultRest
from systemd.wall import Wall
from systemd.search import Search
from systemd.lake import Lake

import errno
import os
import subprocess
import string
import random
secure_random = random.SystemRandom()

class ApplianceManager(object):

  def __init__(self):
    self.store = {}
    self.units = {}
    self.docker = docker.from_env()

    DEVNULL = open(os.devnull, 'w')

    try:
      os.mkdir("/opt/artifacts")
    except OSError as exc:
      if exc.errno != errno.EEXIST:
        raise
      pass

    for service in [
      {
        "name": "lake",
        "wildcard": "lake_*_amd64.deb",
      },
      {
        "name": "vault",
        "wildcard": "vault_*_amd64.deb",
      },
      {
        "name": "wall",
        "wildcard": "wall_*_amd64.deb",
      },
      {
        "name": "search",
        "wildcard": "search_*.deb",
      },
    ]:
      for line in self.docker.api.pull('openbank/{0}'.format(service["name"]), tag='master', stream=True, decode=True):
        progress('docker pull openbank/{0}:master {1}'.format(service["name"], line['status']))

      progress('docker create scratch container openbank/{0}:master'.format(service["name"]))
      container_id = self.docker.api.create_container('openbank/{0}:master'.format(service["name"]), '/bin/false', detach=True)['Id']

      progress('docker cp openbank/{0}:/opt/artifacts /opt/artifacts/{1}'.format(service["name"], service["name"]))
      subprocess.check_call(["docker", "cp", container_id+":/opt/artifacts", "/opt/artifacts/"+service["name"]], stdout=DEVNULL, stderr=subprocess.STDOUT)

      progress('docker remove scratch container openbank/{0}:master'.format(service["name"]))
      self.docker.api.remove_container(container_id)

      packages = subprocess.check_output(["find", "/opt/artifacts/"+service["name"], "-type", "f", "-name", service["wildcard"]], stderr=subprocess.STDOUT).decode("utf-8").strip()

      progress('{0} installing package {1}'.format(service["name"], packages))

      for package in packages.splitlines():
        subprocess.check_call(["apt-get", "-y", "install", "-f", "-qq", "-o=Dpkg::Use-Pty=0", package], stdout=DEVNULL, stderr=subprocess.STDOUT)

      debug('{0} installed'.format(service["name"]))

    DEVNULL.close()

    installed = subprocess.check_output(["systemctl", "-t", "service", "--no-legend"], stderr=subprocess.STDOUT).decode("utf-8").strip()
    services = set([x.split(' ')[0].split('@')[0].split('.service')[0] for x in installed.splitlines()])


    if 'wall' in services:
      self['wall-scale'] = Wall()

    if 'lake' in services:
      self['lake'] = Lake()

    if 'search' in services:
      self['search'] = Search()

    if 'vault' in services:
      self['vault-rest'] = VaultRest()

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

  def onboard_vault(self, tenant=None) -> None:
    if not tenant:
      tenant = ''.join(secure_random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    self['vault-unit'] = VaultUnit(tenant)

  def scale_wall(self, size) -> None:
    for wall in self['wall']:
      wall.scale(size)

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
