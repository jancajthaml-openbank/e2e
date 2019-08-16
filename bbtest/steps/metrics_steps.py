from behave import *
from helpers.eventually import eventually
import os
import json


@then('metrics for tenant {tenant} should report {numberOfAccounts} created accounts')
def step_impl(context, tenant, numberOfAccounts):
  path = '/opt/vault/metrics/metrics.{}.json'.format(tenant)

  @eventually(2)
  def wait_for_file_existence():
    assert os.path.isfile(path)
  wait_for_file_existence()

  actual = dict()
  with open(path, 'r') as fd:
    actual.update(json.loads(fd.read()))

  @eventually(3)
  def wait_for_metrics_update():
    assert actual["createdAccounts"] == numberOfAccounts

  wait_for_metrics_update()
