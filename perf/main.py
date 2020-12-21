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
    pass

  def __exit__(self, *args):
    self.__metrics.persist(self.__label)

def eventually_ready(manager):
  with timeit('waiting until everyone is ready'):
    for units in manager.values():
      for unit in units:
        assert unit.is_healthy, '{} is not healthy {}'.format(unit)
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

  manager = ApplianceManager()

  try:
    info("preparing appliance")
    manager.setup()

    info("preparing integration")
    integration = Integration(manager)

    def on_panic():
      warn('Panic')
      manager.teardown()
      os.kill(os.getpid(), signal.SIGINT)

    info("preparing steps")
    steps = Steps(integration, on_panic)

    info("reconfigure units")
    manager.bootstrap()
    manager.reconfigure({
      'STATSD_ENDPOINT': '127.0.0.1:8125',
      'LOG_LEVEL': 'DEBUG'
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
      with metrics(manager, 's1_new_account_latencies_{0}'.format(total)):
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
        with metrics(manager, 's2_get_account_latencies_{0}'.format(no_accounts)):
          steps.check_balances()
          manager.restart()
        no_accounts += chunk
      debug("scenario finished")

      manager.teardown()
      cleanup()

    ############################################################################

    with timeit('new transaction scenario'):
      total = 20000

      debug("bootstraping appliance")
      manager.bootstrap()

      debug("onboarding services")
      manager.onboard()

      integration.clear()
      eventually_ready(manager)
      debug("appliance ready")

      steps.random_uniform_accounts(100)

      debug("scenario starting")
      with metrics(manager, 's3_new_transaction_latencies_{0}'.format(total)):
        steps.random_uniform_transactions(total)
        manager.restart()
      debug("scenario finished")

      manager.teardown()
      cleanup()

    ############################################################################

    debug("end tests")

  except (KeyboardInterrupt, SystemExit):
    interrupt_stdout()
    warn('Interrupt')
    sys.exit(1)
  except (Exception, AssertionError) as ex:
    warn('Runtime Error {}'.format(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))))
    sys.exit(2)
  finally:
    manager.teardown()
    debug("terminated")
    sys.exit(0)


if __name__ == "__main__":
  with timeit('test run'):
    main()
