from behave import *
import ssl
import urllib.request
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

  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  request = urllib.request.Request(method='POST', url=uri)
  request.add_header('Accept', 'application/json')
  request.add_header('Content-Type', 'application/json')
  request.data = json.dumps(payload).encode('utf-8')

  response = urllib.request.urlopen(request, timeout=10, context=ctx)
  assert response.code in [200, 201]


@given('following transaction is created from tenant {tenant}')
@when('following transaction is created from tenant {tenant}')
def create_transaction_literal(context, tenant):
  uri = "https://127.0.0.1:4401/transaction/{}".format(tenant)

  payload = json.loads(context.text)

  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  request = urllib.request.Request(method='POST', url=uri)
  request.add_header('Accept', 'application/json')
  request.add_header('Content-Type', 'application/json')
  request.data = json.dumps(payload).encode('utf-8')

  response = urllib.request.urlopen(request, timeout=10, context=ctx)
  assert response.code in [200, 201]


@given('{transaction} {transfer} {side} side is forwarded to {tenantTo}/{accountTo} from tenant {tenantFrom}')
@when('{transaction} {transfer} {side} side is forwarded to {tenantTo}/{accountTo} from tenant {tenantFrom}')
def forward_transaction(context, transaction, transfer, side, tenantFrom, tenantTo, accountTo):
  uri = "https://127.0.0.1:4401/transaction/{}/{}/{}".format(tenantFrom, transaction, transfer)

  payload = {
    'side': side,
    'target': {
      'tenant': tenantTo,
      'name': accountTo
    }
  }

  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  request = urllib.request.Request(method='PATCH', url=uri)
  request.add_header('Accept', 'application/json')
  request.add_header('Content-Type', 'application/json')
  request.data = json.dumps(payload).encode('utf-8')

  response = urllib.request.urlopen(request, timeout=10, context=ctx)
  assert response.code in [200, 201]


@given('following transaction is created {times} times from tenant {tenant}')
@when('following transaction is created {times} times from tenant {tenant}')
def forward_transaction(context, times, tenant):
  uri = "https://127.0.0.1:4401/transaction/{}".format(tenant)

  payload = json.loads(context.text)

  for _ in range(int(times)):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    request = urllib.request.Request(method='POST', url=uri)
    request.add_header('Accept', 'application/json')
    request.add_header('Content-Type', 'application/json')
    request.data = json.dumps(payload).encode('utf-8')

    response = urllib.request.urlopen(request, timeout=10, context=ctx)
    assert response.code in [200, 201]
