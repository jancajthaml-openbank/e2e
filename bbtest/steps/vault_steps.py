#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from behave import *
from helpers.eventually import eventually
from helpers.http import Request
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

  request = Request(method='POST', url=uri)
  request.data = json.dumps(payload)
  request.add_header('Content-Type', 'application/json')
  request.add_header('Accept', 'application/json')
  response = request.do()

  assert response.status == 200, 'expected status 200 actual {}'.format(response.status)

@then('{tenant}/{account} balance should be {amount} {currency}')
def account_balance(context, tenant, account, amount, currency):
  uri = "https://127.0.0.1:4400/account/{}/{}".format(tenant, account)

  request = Request(method='GET', url=uri)
  request.add_header('Accept', 'application/json')

  response = request.do()

  assert response.status == 200, 'expected status 200 actual {}'.format(response.status)

  body = json.loads(response.read().decode('utf-8'))

  assert amount == body['balance'], "expected balance {} got {}".format(amount, body['balance'])
  assert currency == body['currency'], "expected currency {} got {}".format(currency, body['currency'])


@then('{tenant}/{account} should exist')
def account_exists(context, tenant, account):
  uri = "https://127.0.0.1:4400/account/{}/{}".format(tenant, account)

  request = Request(method='GET', url=uri)
  request.add_header('Accept', 'application/json')

  response = request.do()

  assert response.status == 200, 'expected status 200 actual {}'.format(response.status)


@then('{tenant}/{account} should not exist')
def account_not_exists(context, tenant, account):
  uri = "https://127.0.0.1:4400/account/{}/{}".format(tenant, account)

  request = Request(method='GET', url=uri)
  request.add_header('Accept', 'application/json')

  response = request.do()

  assert response.status in [404, 504], 'expected status 404 or 504 actual {}'.format(response.status)
