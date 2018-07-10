#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gevent import sleep
import random
from constants import tenants, site
import requests
import ujson as json
from utils import with_deadline

secure_random = random.SystemRandom()

def get_url_data(uri, max_tries=10):
  for n in range(max_tries):
    try:
      return requests.get(uri, timeout=1, verify=False)
    except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
      print("error", e)
      if n == max_tries - 1:
        raise
      sleep(1)

@with_deadline(timeout=10)
def ping():
  url = prepare_health_check()
  return get_url_data(url, max_tries=200).status_code == 200

def prepare_transfer(credit_account_choice, debit_acount_choice, amount_choice):
  account_to = secure_random.choice(credit_account_choice)
  account_from = secure_random.choice(debit_acount_choice)

  # fixme not fixed amount use amount_choice
  return [{
    "credit": account_to,
    "debit": account_from,
    "valuta": "2016-10-28",
    "amount": "1.0",
    "currency": "CZK" # fixme there need to be target tenant
  }]

def prepare_transaction(tenant_name, number_of_transfers, credit_account_choice, debit_acount_choice, amount_choice):
  transfers = []

  for _ in range(number_of_transfers):
    transfers.extend(prepare_transfer(credit_account_choice, debit_acount_choice, amount_choice))

  url = site + '/transaction/' + tenant_name

  body = {
    "transfers": transfers
  }

  return (url, body, json.dumps(body), tenant_name)

def prepare_get_balance(tenant_name, account_name, reference):
  url = site + '/account/' + tenant_name + '/' + account_name
  return (url, reference)

def prepare_health_check():
  return site + '/health'

def prepare_create_account(account_name, is_ballance_check):
  tenant_choice = secure_random.choice(tenants)
  url = site + '/account/' + tenant_choice

  body = {
    "accountNumber": account_name,
    "currency": "CZK",
    "isBalanceCheck": is_ballance_check
  }

  return (url, body, json.dumps(body), tenant_choice)
