#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from gevent import spawn, joinall

import subprocess
import sys
from constants import took, tenant, tenants
import time

def run_command(bash_command, silent=False):
  sys.stdout.write('\033[94m>> bash | \033[0m{0}\n'.format(bash_command))
  start = time.time()
  lines = subprocess.check_output([bash_command], shell=True).decode("utf-8").splitlines()
  took('', time.time() - start, 1)
  return lines

def discover_containers():
  containers = {}
  nodes = run_command("docker ps -a --format \"{{.Image}} {{.ID}}\" --filter \"name=^/performance_\"")

  for node in nodes:
    alias, container = node.split(' ')
    name = alias.split("/")[-1].split(":")[0]
    containers.setdefault(name, []).append(container)

  number_of_vaults = len(containers.get('vault', []))
  for n in range(number_of_vaults):
    tenants.append('{0}_{1}'.format(tenant, n+1))

  return containers

def reset_dockers(containers):
  def task(node):
    run_command("docker container restart {0} 2> /dev/null || :".format(node), True)

  pool = []

  for container in containers.values():
    for node in container:
      pool.append(spawn(task, node))

  joinall(pool)
