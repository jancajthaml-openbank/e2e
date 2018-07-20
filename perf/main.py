#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import partial
from utils import debug, warn, info, interrupt_stdout, clear_dir
from metrics_aggregator import MetricsAggregator
from containers_manager import ContainersManager
from integration.integration import Integration
from steps import Steps
import traceback
from async.pool import Pool

from async.monkey_patch import patch_thread_join
patch_thread_join()

class metrics():

  def __init__(self, label):
    self.__label = label
    self.__metrics = MetricsAggregator("/opt/metrics")
    self.__ready = False
    self.__fn = lambda *args: None

  def __get__(self, instance, *args):
    return partial(self.__call__, instance)

  def __call__(self, *args, **kwargs):
    if not self.__ready:
      self.__fn = args[0]
      self.__ready = True
      return self

    with self:
      return self.__fn(*args, **kwargs)

  def __enter__(self):
    self.__metrics.start()

  def __exit__(self, *args):
    self.__metrics.stop()
    self.__metrics.join()
    self.__metrics.persist(self.__label)

def main():
  debug("starting")

  debug("asserting empty journal, logs and metrics")

  # fixme in parallel please
  clear_dir("/data")
  clear_dir("/logs")
  clear_dir("/opt/metrics")

  manager = ContainersManager()
  integration = Integration(manager)

  def eventually_ready():
    def one_ready(node):
      if not node.is_healthy:
        raise RuntimeError('Health check of {0} failed. Aborting test'.format(node))

    p = Pool()

    debug("waiting until everyone is ready")
    for nodes in manager.values():
      for node in nodes:
        p.enqueue(one_ready, node)

    p.run()
    p.join()

  try:
    # fixme in parallel please :/

    # fixme when spawning wall and vault provide parameter if it should run in memory on be persistant

    # with memory boundaries we could test long running (several days running) tests and determine failures

    debug("spawning components")
    manager.spawn_lake()

    for _ in range(4):
      manager.spawn_vault()

    for _ in range(1):
      manager.spawn_wall()

    for container, images in manager.items():
        info("provisioned {0}({1}x)".format(container, len(images)))

    eventually_ready()

    info("start tests")

    steps = Steps(integration)

    with metrics('random_uniform'):
      steps.random_uniform_accounts(100)
      steps.random_uniform_transactions()
      steps.check_balances()
      manager.reset()

    eventually_ready()

    with metrics('accounts_100'):
      for node in manager['vault']:
        steps.random_targeted_accounts(node.tenant, 100)
      manager.reset()

    eventually_ready()

    with metrics('accounts_1000'):
      for node in manager['vault']:
        steps.random_targeted_accounts(node.tenant, 1000)
      manager.reset()

    eventually_ready()

    with metrics('accounts_5000'):
      for node in manager['vault']:
        steps.random_targeted_accounts(node.tenant, 5000)
      manager.reset()

    eventually_ready()

    # integrity checks
    steps.check_balances()
    steps.balance_cancel_out_check()

    debug("end tests")

  except KeyboardInterrupt:
    interrupt_stdout()
    warn('Interrupt')
  except Exception as ex:
    print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
  finally:
    debug("gracefull teardown components")
    manager.teardown()

    debug("terminated")

if __name__ == "__main__":
  main()
