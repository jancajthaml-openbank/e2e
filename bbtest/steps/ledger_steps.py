#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from behave import *
import json
import time
from helpers.http import Request


@given('{amount} {currency} is transferred from {tenantFrom}/{accountFrom} to {tenantTo}/{accountTo}')
@when('{amount} {currency} is transferred from {tenantFrom}/{accountFrom} to {tenantTo}/{accountTo}')
def create_transaction(context, amount, currency, tenantFrom, accountFrom, tenantTo, accountTo):
  uri = "https://127.0.0.1:4401/transaction/{}".format(tenantFrom)
  payload = {
    'transfers': [{
      'credit': {
        'name': accountTo,
        'tenant': tenantTo,
      },
      'debit': {
        'name': accountFrom,
        'tenant': tenantFrom,
      },
      'amount': amount,
      'currency': currency
    }]
  }

  request = Request(method='POST', url=uri)
  request.add_header('Content-Type', 'application/json')
  request.add_header('Accept', 'application/json')
  request.data = json.dumps(payload)

  response = request.do()

  assert response.status in [200, 201], str(response.status)


@given('following transaction is created {times} times from tenant {tenant}')
@when('following transaction is created {times} times from tenant {tenant}')
def create_transaction_literal_times(context, times, tenant):
  uri = "https://127.0.0.1:4401/transaction/{}".format(tenant)

  request = Request(method='POST', url=uri)
  request.data = context.text
  request.add_header('Content-Type', 'application/json')
  request.add_header('Accept', 'application/json')

  for _ in range(int(times)):
    response = request.do()

    assert response.status in [200, 201], str(response.status)


@given('following transaction is created from tenant {tenant}')
@when('following transaction is created from tenant {tenant}')
def create_transaction_literal(context, tenant):
  create_transaction_literal_times(context, 1, tenant)
