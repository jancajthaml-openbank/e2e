#!/usr/bin/env python

import os
import json
import subprocess
import platform
from functools import lru_cache

class Container(object):

  @property
  def hostname(self) -> str:
    raise NotImplementedError

  @property
  def container(self) -> str:
    raise NotImplementedError

  @staticmethod
  @lru_cache(maxsize=None)
  def get_host_id() -> str:
    return platform.node()

  @staticmethod
  @lru_cache(maxsize=None)
  def get_log_level() -> str:
    return os.environ.get('LOG_LEVEL', 'DEBUG')

  @staticmethod
  @lru_cache(maxsize=None)
  def get_host_network() -> str:
    invoker = Container.get_host_id()

    try:
      net = subprocess.check_output(["/usr/bin/docker", "inspect", "--format=\"{{json .NetworkSettings.Networks}}\"", invoker]).decode("utf-8").strip()
      return next(iter(json.loads(net)))
    except ValueError as ex:
      raise RuntimeError("could not obtain network of host with error : {0}".format(ex))

Container.FNULL = open(os.devnull, 'w')
