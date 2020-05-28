
import os
import sys
from helpers.appliance import ApplianceHelper
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
  context.appliance.cleanup()


def before_all(context):
  context.appliance = ApplianceHelper(context)
  context.http = urllib3.PoolManager()

  os.system('mkdir -p /tmp/reports /tmp/reports/blackbox-tests /tmp/reports/blackbox-tests/logs /tmp/reports/blackbox-tests/metrics')
  os.system('rm -rf /tmp/reports/blackbox-tests/logs/*.log /tmp/reports/blackbox-tests/metrics/*.json')

  try:
    context.appliance.download()
    context.appliance.install()
  except Exception as ex:
    print(ex)
    sys.exit(1)


def after_all(context):
  context.appliance.teardown()
