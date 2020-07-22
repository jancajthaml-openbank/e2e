#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

  @eventually(5)
  def wait_for_metrics_update():
    actual = dict()
    with open(path, 'r') as fd:
      actual.update(json.loads(fd.read()))
    assert actual["createdAccounts"] == numberOfAccounts, 'expected createdAccounts to equal {} but got {}'.format(numberOfAccounts, actual['createdAccounts'])

  wait_for_file_existence()
  wait_for_metrics_update()
