from behave import *
from helpers.eventually import eventually
import urllib3
import json
import time


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

  response = context.http.request('POST', uri, body=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=5)

  assert response.status in [200 , 409]

@then('{tenant}/{account} balance should be {amount} {currency}')
def account_balance(context, tenant, account, amount, currency):
  uri = "https://127.0.0.1:4400/account/{}/{}".format(tenant, account)

  http = urllib3.PoolManager()
  response = http.request('GET', uri, headers={'Accept': 'application/json'}, timeout=5)

  assert response.status == 200

  body = json.loads(response.data.decode('utf-8'))

  assert amount == body['balance'], "expected balance {} got {}".format(amount, body['balance'])
  assert currency == body['currency'], "expected currency {} got {}".format(currency, body['currency'])


@then('{tenant}/{account} should exist')
def account_exists(context, tenant, account):
  uri = "https://127.0.0.1:4400/account/{}/{}".format(tenant, account)

  response = context.http.request('GET', uri, headers={'Accept': 'application/json'}, timeout=5)

  assert response.status == 200


@then('{tenant}/{account} should not exist')
def account_not_exists(context, tenant, account):
  uri = "https://127.0.0.1:4400/account/{}/{}".format(tenant, account)

  response = context.http.request('GET', uri, headers={'Accept': 'application/json'}, timeout=5)

  assert response.status in [404, 504]
