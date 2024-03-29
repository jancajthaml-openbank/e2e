#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from openbank_testkit import StatsdMock
from helpers.appliance import ApplianceHelper
from helpers.logger import logger


def before_feature(context, feature):
  context.statsd.clear()
  context.log.info('')
  context.log.info('  (FEATURE) {}'.format(feature.name))


def before_scenario(context, scenario):
  context.log.info('')
  context.log.info('  (SCENARIO) {}'.format(scenario.name))
  context.log.info('')


def after_scenario(context, scenario):
  context.appliance.collect_logs()


def before_all(context):
  context.log = logger()

  context.statsd = StatsdMock()
  context.statsd.start()

  context.appliance = ApplianceHelper(context)

  try:
    context.log.info('')
    context.log.info('  (STAGE) setup')
    context.log.info('')
    context.appliance.setup()
    context.log.info('')
    context.log.info('  (STAGE) download')
    context.log.info('')
    context.appliance.download()
    context.log.info('')
    context.log.info('  (STAGE) install')
    context.log.info('')
    context.appliance.install()
    context.log.info('')
    context.log.info('  (STAGE) test')
    context.log.info('')
  except Exception as ex:
    print(ex)
    after_all(context)
    sys.exit(1)


def after_all(context):
  context.appliance.teardown()
  context.statsd.stop()
