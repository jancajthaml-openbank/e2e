#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from helpers.appliance import ApplianceHelper
from helpers.statsd import StatsdHelper

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import ssl
try:
  _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
  pass
else:
  ssl._create_default_https_context = _create_unverified_https_context


def after_feature(context, feature):
  context.appliance.collect_logs()


def before_all(context):
  context.statsd = StatsdHelper()
  context.statsd.start()

  context.appliance = ApplianceHelper(context)
  context.http = urllib3.PoolManager()

  try:
    context.appliance.setup()
    context.appliance.download()
    context.appliance.install()
  except Exception as ex:
    print(ex)
    after_all(context)
    sys.exit(1)


def after_all(context):
  context.appliance.teardown()
  context.statsd.stop()
