
import os
from helpers.appliance import ApplianceHelper


def after_feature(context, feature):
  context.appliance.cleanup()


def before_all(context):
  context.appliance = ApplianceHelper(context)

  os.system('mkdir -p /tmp/reports /tmp/reports/blackbox-tests /tmp/reports/blackbox-tests/logs /tmp/reports/blackbox-tests/metrics')
  os.system('rm -rf /tmp/reports/blackbox-tests/logs/*.log /tmp/reports/blackbox-tests/metrics/*.json')

  context.appliance.download()
  context.appliance.install()


def after_all(context):
  context.appliance.teardown()
