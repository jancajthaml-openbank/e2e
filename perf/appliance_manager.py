#!/usr/bin/env python

from systemd.vault import Vault
from systemd.wall import Wall
from systemd.search import Search
from systemd.lake import Lake

import subprocess
import string
import random
secure_random = random.SystemRandom()

class ApplianceManager(object):

  def __init__(self):
    self.store = {}
    self.units = {}

    self['wall'] = Wall()
    self['lake'] = Lake()
    self['search'] = Search()

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
    #self.units.setdefault('vault', []).append(Vault(tenant))
    self['vault'] = Vault(tenant)

  def scale_wall(self, size) -> None:
    for wall in self['wall']:
      wall.scale(size)

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