#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from functools import partial
from utils import debug, warn, info, interrupt_stdout, clear_dir, timeit
from metrics_aggregator import MetricsAggregator
from appliance_manager import ApplianceManager

from integration.integration import Integration
from steps import Steps
import traceback
from parallel.pool import Pool

from time import sleep

from parallel.monkey_patch import patch_thread_join
patch_thread_join()

class metrics():

  def __init__(self, manager, label):
    self.__label = label
    self.__metrics = MetricsAggregator(manager)
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

def eventually_ready(manager):
  debug("waiting until everyone is ready")

  with timeit('eventually_ready'):
    def one_ready(unit):
      if not unit.is_healthy:
        raise RuntimeError('Health check of {0} failed. Aborting test'.format(unit))

    p = Pool()

    for units in manager.values():
      for unit in units:
        p.enqueue(one_ready, unit)

    p.run()
    p.join()

def main():
  debug("starting")

  debug("asserting empty journal, logs and metrics")

  # fixme in parallel please
  clear_dir("/data")
  clear_dir("/reports/perf_logs")
  clear_dir("/reports/perf_metrics")

  info("preparing appliance")
  manager = ApplianceManager()

  info("preparing integration")
  integration = Integration(manager)

  info("preparing steps")
  steps = Steps(integration)

  try:
    # fixme in parallel please :/

    # fixme when spawning wall and vault provide parameter if it should run in memory on be persistant

    # with memory boundaries we could test long running (several days running) tests and determine failures

    #manager.spawn_appliance()
    #manager.spawn_lake()

    info("start tests")

    ############################################################################

    with timeit('new accounts scenario'):
      absolute_total = int(4*1e3)

      for _ in range(4):
        manager.onboard_vault()
      manager.scale_wall(6)
      integration.reset()
      eventually_ready(manager)

      sleep(2)
      with metrics(manager, 's1_new_account_latencies_{0}'.format(absolute_total)):
        steps.random_uniform_accounts(absolute_total)
        manager.reset()
      sleep(2)

      manager.teardown('vault')
      manager.onboard_vault()
      integration.reset()
      eventually_ready(manager)

      absolute_total = int(2*1e3)

      sleep(2)
      with timeit('get accounts scenario'):
        splits = 10
        chunk = int(absolute_total/splits)
        absolute_total = splits*chunk
        no_accounts = chunk

        while no_accounts <= absolute_total:
          steps.random_uniform_accounts(chunk)
          manager.reset('vault')

          with metrics(manager, 's2_get_account_latencies_{0}'.format(no_accounts)):
            steps.check_balances()
            manager.reset()

          no_accounts += chunk
      sleep(2)

      manager.teardown('vault')

    ############################################################################

    with timeit('new transaction scenario'):
      absolute_total = int(10*1e3)

      for _ in range(1):
        manager.onboard_vault()
      manager.scale_wall(6)
      integration.reset()
      manager.reset()
      eventually_ready(manager)

      steps.random_uniform_accounts(100)

      sleep(2)
      with metrics(manager, 's3_new_transaction_latencies_{0}'.format(absolute_total)):
        steps.random_uniform_transactions(absolute_total)
        manager.reset()
      sleep(2)

      manager.teardown('vault')

    ############################################################################

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
  with timeit('test run'):
    main()
