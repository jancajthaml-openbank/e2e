from behave import *
import ssl
import urllib.request
import json
import time
from helpers.eventually import eventually


@given('{activity} {currency} account {tenant}/{account} is created')
@when('{activity} {currency} account {tenant}/{account} is created')
def create_account(context, activity, currency, tenant, account):
  uri = "https://127.0.0.1:4400/account/{}".format(tenant)

  payload = {
    'name': account,
    'format': 'bbtest',
    'currency': currency,
    'isBalanceCheck': activity == "active",
  }
  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  request = urllib.request.Request(method='POST', url=uri)
  request.add_header('Accept', 'application/json')
  request.add_header('Content-Type', 'application/json')
  request.data = json.dumps(payload).encode('utf-8')

  try:
    response = urllib.request.urlopen(request, timeout=10, context=ctx)
    assert response.code == 200
  except urllib.error.HTTPError as err:
    assert err.code == 409


@then('{tenant}/{account} balance should be {amount} {currency}')
def account_balance(context, tenant, account, amount, currency):
  uri = "https://127.0.0.1:4400/account/{}/{}".format(tenant, account)

  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  request = urllib.request.Request(method='GET', url=uri)
  request.add_header('Accept', 'application/json')

  response = urllib.request.urlopen(request, timeout=10, context=ctx)

  assert response.status == 200

  body = json.loads(response.read().decode('utf-8'))

  assert amount == body['balance'], "expected balance {} got {}".format(amount, body['balance'])
  assert currency == body['currency'], "expected currency {} got {}".format(currency, body['currency'])


@then('{tenant}/{account} should exist')
def account_exists(context, tenant, account):
  uri = "https://127.0.0.1:4400/account/{}/{}".format(tenant, account)

  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  request = urllib.request.Request(method='GET', url=uri)
  request.add_header('Accept', 'application/json')

  response = urllib.request.urlopen(request, timeout=10, context=ctx)

  assert response.status == 200


@then('{tenant}/{account} should not exist')
def account_not_exists(context, tenant, account):
  uri = "https://127.0.0.1:4400/account/{}/{}".format(tenant, account)

  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  request = urllib.request.Request(method='GET', url=uri)
  request.add_header('Accept', 'application/json')

  try:
    response = urllib.request.urlopen(request, timeout=10, context=ctx)
  except urllib.error.HTTPError as err:
    assert err.code in [404, 504]
