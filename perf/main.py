#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import signal

from functools import partial
from utils import debug, warn, info, interrupt_stdout, timeit
from metrics.manager import MetricsManager
from appliance_manager import ApplianceManager

from integration.integration import Integration
from steps import Steps
import traceback
from parallel.pool import Pool

from time import sleep

from parallel.monkey_patch import patch_thread_join


patch_thread_join()


class measurement():

  def __init__(self, metrics, label):
    self.__label = label
    self.__ready = False
    self.__metrics = metrics
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
    pass

  def __exit__(self, *args):
    self.__metrics.persist(self.__label)

def eventually_ready(manager):
  with timeit('waiting until everyone is ready'):
    for units in manager.values():
      for unit in units:
        assert unit.is_healthy, '{} is not healthy'.format(unit)
    assert manager.is_healthy, 'manager is not healthy'

def cleanup():
  debug("clearing primary storage")
  os.system('rm -rf /data/*')

def main():
  code = 0

  debug("starting")

  debug("asserting empty data and metrics")

  for path in [
    '/data',
    'reports/perf-tests/metrics',
    'reports/perf-tests/logs'
  ]:
    os.system('mkdir -p {}'.format(path))
    os.system('rm -rf {}/*'.format(path))

  metrics = MetricsManager()
  manager = ApplianceManager()

  info('starting statsd')
  metrics.start()

  info("preparing appliance")
  manager.setup()

  info("preparing integration")
  integration = Integration(manager)

  info("preparing steps")
  steps = Steps(integration)

  info("reconfigure units")
  manager.bootstrap()
  manager.reconfigure({
    'STATSD_ENDPOINT': '127.0.0.1:8125',
    'LOG_LEVEL': 'ERROR'
  })
  manager.teardown()
  cleanup()

  info("start tests")

  ############################################################################

  with timeit('new accounts scenario'):
    total = 10000

    debug("bootstraping appliance")
    manager.bootstrap()

    debug("onboarding services")
    for _ in range(10):
      manager.onboard()

    integration.clear()
    eventually_ready(manager)
    debug("appliance ready")

    debug("scenario starting")
    with measurement(metrics, 's1_new_account_latencies_{0}'.format(total)):
      steps.random_uniform_accounts(total)
      manager.restart()
    debug("scenario finished")

    manager.teardown()
    cleanup()

  with timeit('get accounts scenario'):
    total = 2000

    debug("bootstraping appliance")
    manager.bootstrap()

    debug("onboarding services")
    manager.onboard()

    integration.clear()
    eventually_ready(manager)
    debug("appliance ready")

    splits = 5
    chunk = int(total/splits)
    total = splits*chunk
    no_accounts = chunk

    debug("scenario starting")
    while no_accounts <= total:
      steps.random_uniform_accounts(chunk)
      with measurement(metrics, 's2_get_account_latencies_{0}'.format(no_accounts)):
        steps.check_balances()
        manager.restart()
      no_accounts += chunk
    debug("scenario finished")

    manager.teardown()
    cleanup()

  ############################################################################

  with timeit('new transaction scenario'):
    total = 10000

    debug("bootstraping appliance")
    manager.bootstrap()

    debug("onboarding services")
    manager.onboard()

    integration.clear()
    eventually_ready(manager)
    debug("appliance ready")

    steps.random_uniform_accounts(100)

    debug("scenario starting")
    with measurement(metrics, 's3_new_transaction_latencies_{0}'.format(total)):
      steps.random_uniform_transactions(total)
      manager.restart()
    debug("scenario finished")

    manager.teardown()
    cleanup()

  ############################################################################

  debug("end tests")

  manager.teardown()
  metrics.stop()

  sys.exit(0)


if __name__ == "__main__":
  failed = False
  with timeit('test run'):
    try:
      main()
    except KeyboardInterrupt:
      interrupt_stdout()
      warn('Interrupt')
    except Exception as ex:
      failed = True
      print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
    finally:
      if failed:
        sys.exit(1)
      else:
        sys.exit(0)
