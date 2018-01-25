#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gevent import sleep
from random import choice
from constants import tenant, site
import requests
import ujson as json

def get_url_data(uri, max_tries=10):
  for n in range(max_tries):
    try:
      return requests.get(uri, timeout=1)
    except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
      if n == max_tries - 1:
        raise
      sleep(1)

def ping():
  url = prepare_health_check()
  return get_url_data(url, max_tries=200).status_code == 200

def prepare_transfer(credit_account_choice, debit_acount_choice, amount_choice):
  account_to = choice(credit_account_choice)
  account_from = choice(debit_acount_choice)

  # fixme not fixed amount use amount_choice
  return [{
    "credit": account_to,
    "debit": account_from,
    "valuta": "2016-10-28",
    "amount": "1.0",
    "currency": "CZK"
  }]

def prepare_transaction(number_of_transfers, credit_account_choice, debit_acount_choice, amount_choice):
  transfers = []

  for _ in range(number_of_transfers):
    transfers.extend(prepare_transfer(credit_account_choice, debit_acount_choice, amount_choice))

  url = site + '/v1/sparrow/transaction/' + tenant

  body = {
    "transfers": transfers
  }

  return (url, body, json.dumps(body))

def prepare_get_balance(account_name, reference):
  url = site + '/v1/sparrow/account/' + tenant + '/' + account_name
  return (url, reference)

def prepare_health_check():
  return site + '/health'

def prepare_create_account(account_name, is_ballance_check):
  url = site + '/v1/sparrow/account/' + tenant

  body = {
    "accountNumber": account_name,
    "currency": "CZK",
    "isBalanceCheck": is_ballance_check
  }

  return (url, json.dumps(body))
