#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from behave import *
from helpers.eventually import eventually


@then('metrics for tenant {tenant} should report {numberOfAccounts} created accounts')
def step_impl(context, tenant, numberOfAccounts):
  key = 'openbank.vault.account.created.count#tenant:{}'.format(tenant)

  @eventually(10)
  def wait_for_metrics_update():
    actual = context.statsd.get()
    assert key in actual, 'key {} not found in metrics'.format(key)
    assert str(actual[key]) == str(numberOfAccounts), 'expected createdAccounts to equal {} but got {}'.format(numberOfAccounts, actual[key])

  wait_for_metrics_update()
