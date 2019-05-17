#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from functools import partial
from utils import debug, warn, info, interrupt_stdout, clear_dir, timeit
from metrics.manager import MetricsManager
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
    self.__metrics = MetricsManager(manager)
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

    # with memory boundaries we could test long running (several days running) tests and determine failures

    info("reconfigure units")

    manager.reconfigure({
      'METRICS_REFRESHRATE': '1000ms'
    })

    info("start tests")

    ############################################################################

    with timeit('new accounts scenario'):
      total = 300000

      for _ in range(6):
        manager.onboard()

      integration.reset()
      eventually_ready(manager)

      sleep(1)
      with metrics(manager, 's1_new_account_latencies_{0}'.format(total)):
        steps.random_uniform_accounts(total)
        manager.reset()
        sleep(1)

      manager.teardown('vault-unit')
      manager.teardown('ledger-unit')

    with timeit('get accounts scenario'):
      total = 1000

      manager.onboard()

      integration.reset()
      eventually_ready(manager)

      splits = 10
      chunk = int(total/splits)
      total = splits*chunk
      no_accounts = chunk

      while no_accounts <= total:
        steps.random_uniform_accounts(chunk)
        manager.reset('vault-unit')
        manager.reset('vault-rest')

        sleep(1)
        with metrics(manager, 's2_get_account_latencies_{0}'.format(no_accounts)):
          steps.check_balances()
          manager.reset()
          sleep(1)

        no_accounts += chunk

      manager.teardown('vault-unit')
      manager.teardown('ledger-unit')

    ############################################################################

    with timeit('new transaction scenario'):
      total = 50000

      manager.onboard()

      integration.reset()
      manager.reset()
      eventually_ready(manager)

      steps.random_uniform_accounts(40)

      sleep(1)
      with metrics(manager, 's3_new_transaction_latencies_{0}'.format(total)):
        steps.random_uniform_transactions(total)
        manager.reset()
        sleep(1)

      manager.teardown('vault-unit')
      manager.teardown('ledger-unit')

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
