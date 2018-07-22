#!/usr/bin/env python

from docker.vault import Vault
from docker.lake import Lake
from docker.wall import Wall

class ContainersManager(object):

  def __init__(self):
    self.store = {}
    self.containers = {}

  def __len__(self):
    return sum([len(x) for x in self.containers.values()])

  def __getitem__(self, key):
    return self.containers.get(str(key), [])

  def __delitem__(self, key):
    # fixme add lock here
    if not str(key) in self.containers:
      return

    for node in self.containers[str(key)]:
      node.teardown()

    del self.containers[str(key)]

  def items(self) -> list:
    return self.containers.items()

  def values(self) -> list:
    return self.containers.values()

  def reset(self, key=None) -> None:
    if not key:
      for name in list(self.containers):
        for node in self[name]:
          node.restart()
      return

    for node in self[key]:
      node.restart()

  def teardown(self, key=None) -> None:
    if key:
      del self[key]
    else:
      for name in list(self.containers):
        del self[name]

  def spawn_vault(self, *args) -> None:
    instance = Vault(*args)
    self.containers.setdefault('vault', []).append(instance)

  def spawn_lake(self) -> None:
    instance = Lake()
    self.containers.setdefault('lake', []).append(instance)

  def spawn_wall(self) -> None:
    instance = Wall()
    self.containers.setdefault('wall', []).append(instance)

