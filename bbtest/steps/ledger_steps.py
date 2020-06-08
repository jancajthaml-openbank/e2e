from behave import *
import urllib3
import json
import time
from helpers.eventually import eventually


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

  response = context.http.request('POST', uri, body=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=5)

  assert response.status in [200, 201]


@given('following transaction is created from tenant {tenant}')
@when('following transaction is created from tenant {tenant}')
def create_transaction_literal(context, tenant):
  uri = "https://127.0.0.1:4401/transaction/{}".format(tenant)

  payload = json.loads(context.text)

  response = context.http.request('POST', uri, body=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=5)

  assert response.status in [200, 201]


@given('following transaction is created {times} times from tenant {tenant}')
@when('following transaction is created {times} times from tenant {tenant}')
def forward_transaction(context, times, tenant):
  uri = "https://127.0.0.1:4401/transaction/{}".format(tenant)

  payload = json.loads(context.text)

  for _ in range(int(times)):
    response = context.http.request('POST', uri, body=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=5)

    assert response.status in [200, 201]
